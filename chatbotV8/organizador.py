import google.generativeai as genai
from pathlib import Path
from backend.from_to_mysql import from_mysql_extrair
import pandas as pd
import os

diretorio = Path(__file__).resolve().parent.parent
caminho_arquivos = diretorio / "backend" /"uploads"

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

def pesquisar(id_file, search=None):
    # Pesquisar em qual arquivo está uma palavra chave
    #path_file = caminho_arquivos / id_file

    #from_mysql_extrair(id_file)

    #tabela = pd.read_excel(path_file)

    #print(tabela)

    return f"Pesquisando '{search}' no arquivo..."

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

if __name__ == '__main__':
    id_file = '7e93132d-e9cd-405a-ab0b-540eec0b6802.xlsx'
    search = 'Estabelecer requisitos de shelf life'
    pesquisar(id_file, search)