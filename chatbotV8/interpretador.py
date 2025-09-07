import random
from .organizador import organizar, chat_avancado
from .treinar import termos_chaves, respostas_termos

"""
    Esse arquivo lida com a interpretação das mensagens do usuário e a construção da respostas
"""

def interpretar(mensagem, usuario, modo_chat):
    mensagem = mensagem.lower()

    # Se já estiver em modo avançado, só desativa se a pessoa pedir "sair"
    if modo_chat == 'avancado':
        if "sair" in mensagem:
            return "Ok, desativando o modo avançado. Como posso te ajudar com as tarefas normais?", "standard"
        else:
            resposta_gemini = chat_avancado(mensagem)
            return resposta_gemini, "avancado"  # Mantém avançado até o "sair"

    # Modo standard
    chaves = termos_chaves()
    respostas = respostas_termos()
    msg_chave = set()

    for frase_chave, termo_associado in chaves.items():
        if frase_chave in mensagem:
            msg_chave.add(termo_associado)

    # Se não encontrou nada
    if not msg_chave:
        return "Desculpe, não entendi. Você pode tentar reformular sua pergunta ou pedir 'ajuda'.", 'standard'

    # Verifica se o usuário pediu para ativar o avançado
    if 'chat_avancado' in msg_chave:
        resposta = construir_frase(list(msg_chave), usuario, respostas)
        return resposta, 'avancado'  # ativa avançado para próximas interações

    # Resposta normal
    resposta = construir_frase(list(msg_chave), usuario, respostas)
    return resposta, 'standard'


def construir_frase(chaves, usuario, respostas):
    trechos_resposta = [] # Armazena os trechos da resposta que foi construída
    prefixo = " " # Adicionado no começo das resposta da Liora
    
    # Passa por todos os termos chaves da mensagem, ex. ['cumprimentar', 'minhas_tarefas'...]
    for chave in chaves:
        if chave in respostas:
            # Vai pegar a chave e buscar no dicionário que armazena as respostas com base na chave
            processo = respostas[chave]

            # Verifica se a resposta para a mensagem é uma demanda/ação (int) ou um mensagem resposta (string)
            if isinstance(processo, int):
                trecho = organizar(processo, usuario)
                trechos_resposta.append(trecho)
            elif isinstance(processo, str):
                trechos_resposta.append(processo)
        else:
            trechos_resposta.append(f"Desculpe, não encontrei uma resposta para '{chave}'.")

    return prefixo + ".\n".join(trechos_resposta)