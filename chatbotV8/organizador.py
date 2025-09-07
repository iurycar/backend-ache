import google.generativeai as genai
from pathlib import Path
import pandas as pd
import os

diretorio = Path(__file__).parent
caminho_arquivos = diretorio / "dados" / "uploads"

# Configurar a API do Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Inicializa o modelo
model = genai.GenerativeModel('gemini-1.5-flash')
chat_session = model.start_chat(history=[])

def organizar(processo, usuario, *args):
    match processo:
        case 1:
            return "🤖 Modo avançado da Melora ativado. (Digite 'sair' para desativar esse modo). Por favor, digite sua mensagem."
        case 2:
            return pesquisar(args)
        case 3:
            return filtrar(args)
        case 4:
            return alterar(args)
        case 5:
            return "Você pode escrever 'modo avançado' para tarefas mais complexas. Ou escolher algum das opções abaixo:"
        case _:
            return "Desculpe, não sei como lidar com essa solicitação."

def pesquisar(buscando):
    # Pesquisar em qual arquivo está uma palavra chave
    return f"Pesquisando '{buscando}' no arquivo..."

def filtrar(filtro):
    # Filtrar palavras chaves nas planilhas
    return f"Filtrando '{filtro}' no arquivo..."

def alterar(mudar):
    # Alterar trechos das planilhas
    return f"Alterando o arquivo..."

def chat_avancado(mensagem):
    # Prompt inicial
    prompt_base = "Você é a Melora, uma assistente virtual especializada em cronogramas modulares e gestão de projetos. Responda de forma amigável e útil para a seguinte pergunta:"

    try:
        # Envia a mensagem do usuário para o chat do Gemini com o prompt
        resposta = chat_session.send_message(f"{prompt_base}\n{mensagem}")
        return resposta.text
    except Exception as error:
        return f"Desculpe, ocorreu um erro de comunicação: {error}"
