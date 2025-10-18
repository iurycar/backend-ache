from .learn import get_keywords, get_response_keywords
from .handle_demands import demands, advanced_chat
from .ahoCorasick import Automaton
from collections import deque
import random
import re

"""
    Esse arquivo lida com a interpretação das mensagens do usuário e a construção da respostas
"""

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
        else:
            resposta_gemini = advanced_chat(mensagem)
            return resposta_gemini, "avancado"  # Mantém avançado até o "sair"

    # Utilizando o que a professora Patricia ensinou em aula, podemos criar uma trie para buscar as palavras chaves
    # Tem o Algoritmo Aho-corasick que seria o ideal
    encontrados = TRIE.find_values(mensagem)  # Encontra as palavras chaves na mensagem
    msg_chave: deque[str] = deque(encontrados)   # Cria um conjunto

    print(f"Palavras chaves encontradas na mensagem: {msg_chave}")

    # Se não encontrou nada
    if not msg_chave:
        return "Desculpe, não entendi. Você pode tentar reformular sua pergunta ou pedir 'ajuda'.", 'standard'

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
        chave = chaves.popleft()
        
        if chave in RESPOSTAS:
            # Vai pegar a chave e buscar no dicionário que armazena as respostas com base na chave
            processo = RESPOSTAS[chave]

            # Verifica se a resposta para a mensagem é uma demanda/ação (int) ou um mensagem resposta (string)
            if isinstance(processo, int):
                trecho = demands(processo, mensagem, usuario)
                trechos_resposta.append(trecho)
            elif isinstance(processo, str):
                trechos_resposta.append(processo)
        else:
            trechos_resposta.append(f"Desculpe, não encontrei uma resposta para '{chave}'.")

    return prefixo + ".\n".join(trechos_resposta)