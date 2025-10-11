from backend.from_to_mysql import from_mysql_extrair
from .tarefas import adicionar_tarefa
import google.generativeai as genai
from backend.db import consultaSQL
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

def organizar(processo: str, mensagem: str, usuario: str, *args: str) -> str:
    # Função principal que organiza as tarefas
    match processo:
        case 1:
            return "🤖 Modo avançado da Melora ativado. (Digite 'sair' para desativar esse modo). Por favor, digite sua mensagem."
        case 2:
            return alterar(args)
        case 3:
            return filtrar(args)
        case 4:
            return pesquisar(args)
        case 5:
            return ajudar(args)
        case 6:
            return adicionar_tarefa(mensagem)
        case 7:
            return adicionar_evento(mensagem)
        case _:
            return "Desculpe, não sei como lidar com essa solicitação."


def pesquisar(id_file: str, search=None) -> str:
    # Pesquisar em qual arquivo está uma palavra chave
    #path_file = caminho_arquivos / id_file

    #from_mysql_extrair(id_file)

    #tabela = pd.read_excel(path_file)

    #print(tabela)

    return f"Pesquisando '{search}' no arquivo..."


def filtrar(filtro: str) -> str:
    # Filtrar palavras chaves nas planilhas
    return f"Filtrando '{filtro}' no arquivo..."


def alterar(mudar: str) -> str:
    # Alterar trechos das planilhas
    return f"Alterando o arquivo..."


def chatAvancado(mensagem: str) -> str:
    # Prompt inicial
    prompt_base = "Você é a Melora, uma assistente virtual especializada em cronogramas modulares e gestão de projetos. Responda de forma amigável e útil para a seguinte pergunta:"

    try:
        # Envia a mensagem do usuário para o chat do Gemini com o prompt
        resposta = chat_session.send_message(f"{prompt_base}\n{mensagem}")
        return resposta.text
    except Exception as error:
        return f"Desculpe, ocorreu um erro de comunicação: {error}"


def ajudar(assunto: str) -> str:
    # Fornece ajuda sobre como usar o chatbot
    return f"Você pediu ajuda sobre '{assunto}'. Como posso ajudar você?"

if __name__ == '__main__':
    #dados = adicionar_tarefa("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Desafio_Número_1_Projeto_1_-_Exportado.xlsx")
    #dados = adicionar_tarefa("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Projeto 1")
    #print(dados)
    pass