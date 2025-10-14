from backend.from_to_mysql import from_mysql_extrair
import google.generativeai as genai
from .handle_tasks import add_task
from pathlib import Path
import pandas as pd
import os

diretorio = Path(__file__).resolve().parent.parent
caminho_arquivos = diretorio / "backend" /"uploads"

# Configurar a API do Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Inicializa o modelo
model = genai.GenerativeModel('gemini-2.5-flash')
chat_session = model.start_chat(history=[])

def demands(processo: str, mensagem: str, usuario: str, *args: str) -> str:
    """ Função que lida com diferentes demandas do usuário. 
    @param processo: Tipo de processo a ser executado (1-7).
    @param mensagem: Mensagem do usuário.
    @param usuario: Nome do usuário.
    @param args: Argumentos adicionais necessários para alguns processos.
    
    @return: Resposta do chatbot.
    """
    
    # Função principal que organiza as tarefas
    match processo:
        case 1:
            return "🤖 Modo avançado da Melora ativado. (Digite 'sair' para desativar esse modo). Por favor, digite sua mensagem."
        case 2:
            return altering(args)
        case 3:
            return filtering(args)
        case 4:
            return searching(args)
        case 5:
            return helping(args)
        case 6:
            return add_task(mensagem)
        case 7:
            return add_event(mensagem)
        case _:
            return "Desculpe, não sei como lidar com essa solicitação."


def searching(id_file: str, search=None) -> str:
    # Pesquisar em qual arquivo está uma palavra chave
    #path_file = caminho_arquivos / id_file

    #from_mysql_extrair(id_file)

    #tabela = pd.read_excel(path_file)

    #print(tabela)

    return f"Pesquisando '{search}' no arquivo..."


def filtering(filtro: str) -> str:
    # Filtrar palavras chaves nas planilhas
    return f"Filtrando '{filtro}' no arquivo..."


def altering(mudar: str) -> str:
    # Alterar trechos das planilhas
    return f"Alterando o arquivo..."


def advanced_chat(mensagem: str) -> str:
    # Prompt inicial
    prompt_base = "Você é a Melora, uma assistente virtual especializada em cronogramas modulares e gestão de projetos. Responda de forma amigável e útil para a seguinte pergunta:"

    try:
        # Envia a mensagem do usuário para o chat do Gemini com o prompt
        resposta = chat_session.send_message(f"{prompt_base}\n{mensagem}")
        return resposta.text
    except Exception as error:
        return f"Desculpe, ocorreu um erro de comunicação: {error}"


def helping(assunto: str) -> str:
    # Fornece ajuda sobre como usar o chatbot
    return f"Você pediu ajuda sobre '{assunto}'. Como posso ajudar você?"

if __name__ == '__main__':
    #dados = add_tasks("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Desafio_Número_1_Projeto_1_-_Exportado.xlsx")
    #dados = add_tasks("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Projeto 1")
    #print(dados)
    pass