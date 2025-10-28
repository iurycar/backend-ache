from .learn import get_keywords, get_response_keywords
from .handle_demands import demands, advanced_chat
from .ahoCorasick import Automaton
from collections import deque
import unicodedata
import random
import re

"""
    Esse arquivo lida com a interpretação das mensagens do usuário e a construção da respostas
"""

def normalize_boundaries(text: str) -> str:
    msg = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')
    msg = re.sub(r'[^a-z]+', ' ', msg)      # Remove caracteres especiais, mantendo apenas letras e espaços
    msg = re.sub(r'\s+', ' ', msg).strip()  # Normaliza espaços em branco, removendo espaços extras
    return f' {msg} '

# Carrega os dados treinados
CHAVES: dict[str, list[str]] = get_keywords() # Dicionário com as palavras chaves
RESPOSTAS: dict[str, str | int] = get_response_keywords() # Dicionário com as respostas associadas as palavras chaves

TRIE = Automaton() # Cria o automato
for demanda, termos in CHAVES.items(): # Palavras chaves para adicionar na trie
    for termo in termos:
        TRIE.add_string(termo, demanda)

def get_intention(mensagem: str, usuario: str, modo_chat: str) -> tuple[str, str]:
    """ Função que interpreta a mensagem do usuário e decide a resposta apropriada.
    @param mensagem: Mensagem do usuário.
    @param usuario: Nome do usuário.
    @param modo_chat: Modo atual do chat ('standard' ou 'avancado').
    @return: Tupla contendo a resposta do chatbot e o modo de chat atualizado.
    """

    mensagem = mensagem.lower()
    mensagem = re.sub(r'\s+', ' ', mensagem) # Normaliza espaços em branco, removendo espaços extras

    # Se já estiver em modo avançado, só desativa se a pessoa pedir "sair"
    if modo_chat == 'avancado':
        if "sair" in mensagem:
            return "Ok, desativando o modo avançado. Como posso te ajudar com as tarefas normais?", "standard"

    # Utilizando o que a professora Patricia ensinou em aula, podemos criar uma trie para buscar as palavras chaves
    # Tem o Algoritmo Aho-corasick que seria o ideal
    
    # Verifica se as palavras da mensagem estão na trie
    encontrados = TRIE.find_values(mensagem)  # Encontra as palavras chaves na mensagem
    msg_chave: list[str] = list(encontrados)   # Cria um conjunto

    # Garantir que não haja falso positivos, como por exemplo, 'oi' em 'coisas'
    msg_normalize = normalize_boundaries(mensagem)
    filtradas: set[str] = set()
    
    for demanda in msg_chave: # Pega todas as demandas encontradas na mensagem
        termos_demandas = CHAVES.get(demanda, []) # Pega a lista de palavras associada a essa demanda
        
        for termo in termos_demandas:   # Pega um termo dentro dessa lista de palavras
            termo_normalizado = normalize_boundaries(termo)
            
            if termo_normalizado in msg_normalize:
                filtradas.add(demanda)
                break

    msg_chave = deque(filtradas)

    print(f"Palavras chaves encontradas na mensagem: {msg_chave}")

    # Se não encontrou nada
    if not msg_chave:
        return "Desculpe, não entendi. Você pode tentar reformular sua pergunta ou pedir 'ajuda'.", 'standard'

    if modo_chat == 'avancado':
        resposta_gemini = advanced_chat(mensagem, msg_chave, usuario)
        return resposta_gemini, "avancado"  # Mantém avançado até o "sair"

    # Verifica se o usuário pediu para ativar o avançado
    if 'chat_avancado' in msg_chave:
        resposta = build_response(mensagem, msg_chave, usuario)
        return resposta, 'avancado'  # ativa avançado para próximas interações

    if 'debug' in msg_chave:
        print(f"DEBUG INFO:\nMensagem original: '{mensagem}'\nPalavras chaves: {list(msg_chave)}\nUsuário: '{usuario}'\nModo chat atual: '{modo_chat}'\nAutomato: {TRIE.show_trie()}\n")

    # Resposta normal
    resposta = build_response(mensagem, msg_chave, usuario)
    return resposta, 'standard'


def build_response(mensagem: str, chaves: deque[str], usuario: str) -> str:
    """ Constrói a resposta do chatbot com base nas palavras chaves encontradas na mensagem.
    @param mensagem: Mensagem do usuário.
    @param chaves: Lista de palavras chaves encontradas na mensagem.
    @param usuario: Nome do usuário.
    @return: Resposta do chatbot."""

    trechos_resposta: list[str] = [] # Armazena os trechos da resposta que foi construída
    prefixo: str = ' ' # Adicionado no começo das resposta da Liora
    
    # Passa por todos os termos chaves da mensagem, ex. ['cumprimentar', 'minhas_tarefas'...]
    while len(chaves) > 0:
        demanda = chaves.popleft()

        if demanda in RESPOSTAS:
            # Vai pegar a chave e buscar no dicionário que armazena as respostas com base na chave
            processo = RESPOSTAS[demanda]
            
            # Verifica se a resposta para a mensagem é uma demanda/ação (int) ou um mensagem resposta (string)
            if isinstance(processo, int):
                trecho = demands(processo, mensagem, usuario)
                trechos_resposta.append(trecho)
            
            elif isinstance(processo, str):
                trechos_resposta.append(processo)

            elif isinstance(processo, list):
                if len(chaves) >= 1 or len(trechos_resposta) > 0:
                    trechos_resposta.append(processo[1]+'\n')
                else:
                    trechos_resposta.append(processo[0]+'\n')
        else:
            trechos_resposta.append(f"Desculpe, não encontrei uma resposta para '{demanda}'.")

    #print(f"Trechos de resposta gerados: {trechos_resposta}")
    return prefixo + "\n".join(trechos_resposta)