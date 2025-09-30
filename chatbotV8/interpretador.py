from .organizador import organizar, chat_avancado
from .treinar import termos_chaves, respostas_termos
import random
import re

"""
    Esse arquivo lida com a interpretação das mensagens do usuário e a construção da respostas
"""

def interpretar(mensagem: str, usuario: str, modo_chat: str) -> tuple[str, str]:
    mensagem = mensagem.lower()
    mensagem = re.sub(r'\s+', ' ', mensagem) # Normaliza espaços em branco, removendo espaços extras

    # Se já estiver em modo avançado, só desativa se a pessoa pedir "sair"
    if modo_chat == 'avancado':
        if "sair" in mensagem:
            return "Ok, desativando o modo avançado. Como posso te ajudar com as tarefas normais?", "standard"
        else:
            resposta_gemini = chat_avancado(mensagem)
            return resposta_gemini, "avancado"  # Mantém avançado até o "sair"

    chaves = termos_chaves() # Dicionário com as palavras chaves
    respostas = respostas_termos() # Dicionário com as respostas associadas as palavras chaves
    msg_chave = set()   # Cria um conjunto

    for frase_chave, termo_associado in chaves.items():
        key = frase_chave.lower().strip()
        # Cria uma expressão regular para corresponder exatamente a palavra chave
        pattern = rf'\b{re.escape(key)}\b' # Evita falsos positivos, ex. "oi" em "coisas"

        if re.search(pattern, mensagem):
            msg_chave.add(termo_associado)

    # Se não encontrou nada
    if not msg_chave:
        return "Desculpe, não entendi. Você pode tentar reformular sua pergunta ou pedir 'ajuda'.", 'standard'

    # Verifica se o usuário pediu para ativar o avançado
    if 'chat_avancado' in msg_chave:
        resposta = construir_frase(mensagem, list(msg_chave), usuario, respostas)
        return resposta, 'avancado'  # ativa avançado para próximas interações

    # Resposta normal
    resposta = construir_frase(mensagem, list(msg_chave), usuario, respostas)
    return resposta, 'standard'


def construir_frase(mensagem: str, chaves: str, usuario: str, respostas: str) -> str:
    trechos_resposta:list[str] = [] # Armazena os trechos da resposta que foi construída
    prefixo: str = ' ' # Adicionado no começo das resposta da Liora
    
    # Passa por todos os termos chaves da mensagem, ex. ['cumprimentar', 'minhas_tarefas'...]
    for chave in chaves:
        if chave in respostas:
            # Vai pegar a chave e buscar no dicionário que armazena as respostas com base na chave
            processo = respostas[chave]

            # Verifica se a resposta para a mensagem é uma demanda/ação (int) ou um mensagem resposta (string)
            if isinstance(processo, int):
                trecho = organizar(processo, mensagem, usuario)
                trechos_resposta.append(trecho)
            elif isinstance(processo, str):
                trechos_resposta.append(processo)
        else:
            trechos_resposta.append(f"Desculpe, não encontrei uma resposta para '{chave}'.")

    return prefixo + ".\n".join(trechos_resposta)