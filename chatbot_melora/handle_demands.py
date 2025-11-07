import google.generativeai as genai
from collections import deque
from pathlib import Path
import pandas as pd
import datetime
import os 
import re

from .handle_tasks import add_task, my_tasks, how_to_do

from backend.services.from_to_mysql import from_mysql_extrair
from backend.services.db import consultaSQL

diretorio = Path(__file__).resolve().parent.parent
caminho_arquivos = diretorio / "backend" / "data"
caminho_arquivos.mkdir(parents=True, exist_ok=True)

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
            return my_tasks(mensagem, usuario)
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
        case 8:
            return how_to_do(mensagem, usuario)
        case 9:
            return send_email(mensagem, usuario)
        case _:
            return "Desculpe, não sei como lidar com essa solicitação."


def searching(id_file: str, search=None) -> str:
    # Pesquisar palavras chaves no banco de dados
    # Limitar para a tabela 'SHEETS' e 'PROJECTS'

    return f"Pesquisando '{search}' no arquivo..."


def filtering(filtro: str) -> str:
    # Filtrar palavras chaves nas planilhas
    return f"Filtrando '{filtro}' no arquivo..."


def send_email(mensagem: str, usuario: str) -> str:
    pass


def helping(assunto: str) -> str:
    # Fornece ajuda sobre como usar o chatbot
    return f"Você pediu ajuda sobre '{assunto}'. Como posso ajudar você?"


def advanced_chat(mensagem: str, chaves: deque[str], usuario: str) -> str:
    # Prompt inicial
    prompt_base = """Você é a Melora, uma assistente virtual especializada em cronogramas modulares e gestão de projetos."""

    if len(chaves) > 0:
        prompt_base += "Os dados relevantes para esta conversa são: "
        while len(chaves) > 0:
            chave = chaves.popleft()
            
            # Busca a informação relevante no banco de dados ou arquivos
            if chave == 'minhas_tarefas':
                tarefas = my_tasks(mensagem, usuario).replace('Suas tarefas atuais são:\n', ' ')
                prompt_base += f"{tarefas}"
            elif chave == 'como_fazer':
                instrucoes = how_to_do(mensagem, usuario)
                prompt_base += f"{instrucoes}"

    prompt_base += "Responda de forma amigável e útil para a seguinte pergunta:"

    try:
        # Envia a mensagem do usuário para o chat do Gemini com o prompt
        resposta = chat_session.send_message(f"{prompt_base}\n{mensagem}")
        
        print("Prompt enviado ao Gemini:", prompt_base+"\n"+mensagem)
        print("Resposta do Gemini:", resposta.text)
        return resposta.text
    except Exception as error:
        return f"Desculpe, ocorreu um erro de comunicação: {error}"

if __name__ == '__main__':
    #dados = add_tasks("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Desafio_Número_1_Projeto_1_-_Exportado.xlsx")
    #dados = add_tasks("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Projeto 1")
    #print(dados)
    pass