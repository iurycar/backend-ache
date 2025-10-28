from backend.from_to_mysql import from_mysql_extrair
import google.generativeai as genai
from .handle_tasks import add_task
from backend.db import consultaSQL
from collections import deque
from pathlib import Path
import pandas as pd
import datetime
import pypdf
import os
import re

diretorio = Path(__file__).resolve().parent.parent
caminho_arquivos = diretorio / "backend" / "uploads"

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
        case _:
            return "Desculpe, não sei como lidar com essa solicitação."


def searching(id_file: str, search=None) -> str:
    # Pesquisar palavras chaves no banco de dados
    # Limitar para a tabela 'SHEETS' e 'PROJECTS'

    return f"Pesquisando '{search}' no arquivo..."


def filtering(filtro: str) -> str:
    # Filtrar palavras chaves nas planilhas
    return f"Filtrando '{filtro}' no arquivo..."


def my_tasks(mensagem, usuario) -> str:
    # Selecionar as tarefas do usuário
    # Filtrar as tarefas em que o prazo é curto (3 dias ou menos)
    # Filtrar por prioridade ('Sempre', 'A', 'B' e 'C')
    resposta: str = "Suas tarefas atuais são:\n"

    #print('Buscando tarefas para o usuário:', usuario)

    tarefas: list[dict] = consultaSQL(
        'SELECT', 'SHEETS',
        where={'user_id': usuario},
        where_especial={'conclusion': '< 1'},
        campo={'JOIN ON': ['PROJECTS', 'id_file']},
        colunas_dados={
            'num': None,
            'start_date': None,
            'deadline': None,
            'status': None,
            'project_name': None
        }
    )

    #print('Tarefas encontradas:', tarefas)
    if not tarefas:
        return "Você não possui tarefas pendentes no momento."

    for tarefa in tarefas:
        tarefa['nome'] = f"Tarefa {tarefa.get('num', 'Desconhecida')}"
        tarefa['prioridade'] = tarefa.get('status', 'Desconhecida')

        # ex. deadline = '2025-09-13 21:45:31'
        deadline = tarefa.get('deadline', '')

        if isinstance(deadline, datetime.datetime):
            dt_deadline = deadline
        elif isinstance(deadline, str):
            try:
                dt_deadline = datetime.datetime.fromisoformat(deadline)
            except Exception:
                continue
        else:
            continue

        now = datetime.datetime.now(dt_deadline.tzinfo)

        delta = dt_deadline - now
        dias = abs(delta.days)

        if delta.total_seconds() < 0:
            tarefa['prazo'] = f'Atrasada em {dias} dias'
        else:
            tarefa['prazo'] = f'Faltam {dias} dias'

        resposta += f"-> {tarefa['nome']} do projeto {tarefa['project_name']} ({tarefa['prazo']}, Prioridade: {tarefa['prioridade']})\n"
        resposta += "--------------------------\n"

    #print('Resposta gerada:', resposta)

    return resposta


def how_to_do(mensagem: str, usuario: str) -> str:
    # Exemplo de mensagem: "Como faço a tarefa 4 do projeto 1?"
    # Extrai a tarefa e o projeto da mensagem
    tarefa = re.search(r'tarefa (\d+)', mensagem)
    projeto = re.search(r'projeto (\d+)', mensagem)

    if tarefa and projeto:
        task = tarefa.group(1)
        proj = projeto.group(1)
    else:
        return "Desculpe, não consegui identificar a tarefa e/ou o projeto."

    resposta = f"Para fazer a tarefa {task} do projeto {proj}, siga as instruções abaixo:\n\n"

    # Buscar o texto referência no banco de dados
    texto: list[dict] = consultaSQL(
        'SELECT', 'SHEETS',
        where={'num': task, 'project_name': proj},
        campo={'JOIN ON': ['PROJECTS', 'id_file']},
        colunas_dados={
            'text': None
        }  
    )

    if texto:
        # Retorna, por exemplo, 'texto.2'
        texto_ref = texto[0]['text']

        if not texto_ref:
            return f"Desculpe, não consegui encontrar as instruções para a tarefa {task}."
    else:
        return f"Desculpe, não consegui encontrar as instruções para a tarefa {task}."

    """ Esse trecho está funcionando para PDFs armazenados localmente. Quando resolver o problema de
    acesso do SharePoint, deve ser adaptado para baixar o arquivo do SharePoint e depois ler o PDF. """ 

    # Carregar o caminho do arquivo PDF
    # TODO: Implementar o download do PDF do SharePoint
    arquivo_pdf = caminho_arquivos / f"Doc.Teste.pdf"

    # Buscar no PDF o texto referência, por exemplo, 'texto.2'
    # Usar o pypdf para extrair o texto do PDF e procurar pelo texto referência
    with pypdf.PdfReader(str(arquivo_pdf)) as pdf:
        texto_extraido = ""
        
        for pagina in pdf.pages:
            texto_extraido += (pagina.extract_text() or "") + "\n"
    
    match_ref = re.search(r'texto\.?\s*(\d+)', texto_ref, flags=re.IGNORECASE)
    
    if not match_ref:
        return f"Desculpe, o texto de referência '{texto_ref}' é inválido."
    ref_num = match_ref.group(1)

    # Procurar o texto referência no texto extraído
    # Deve parar quando encontrar o próximo texto referência ou o final do documento
    texto_pattern = rf"(?is)\btexto\.?\s*{ref_num}\s*[:.]?\s*(.*?)(?=\btexto\.?\s*\d+\s*[:.]?|\Z)"
    match = re.search(texto_pattern, texto_extraido)
    
    if match:
        instrucoes = match.group(1).strip().lower().replace('\n', ' ').split('.')
    else:
        return f"Desculpe, não consegui encontrar as instruções para a tarefa {task} no documento."

    print('Instruções encontradas:', instrucoes)

    for instrucao in instrucoes:
        if instrucao.strip() in ['.', '', ' ']:
            continue
        
        resposta += f"• {instrucao.strip().capitalize()}.\n"

    return resposta

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