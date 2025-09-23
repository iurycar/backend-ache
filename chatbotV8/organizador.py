#from backend.from_to_mysql import from_mysql_extrair
import google.generativeai as genai
from pathlib import Path
import pandas as pd
import re
import os

diretorio = Path(__file__).resolve().parent.parent
caminho_arquivos = diretorio / "backend" /"uploads"

# Configurar a API do Gemini
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Inicializa o modelo
model = genai.GenerativeModel('gemini-1.5-flash')
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
            return "Você pode escrever 'modo avançado' para tarefas mais complexas. Ou escolher algum das opções abaixo:"
        case 6:
            return adicionarTarefa(mensagem)
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

def chat_avancado(mensagem: str) -> str:
    # Prompt inicial
    prompt_base = "Você é a Melora, uma assistente virtual especializada em cronogramas modulares e gestão de projetos. Responda de forma amigável e útil para a seguinte pergunta:"

    try:
        # Envia a mensagem do usuário para o chat do Gemini com o prompt
        resposta = chat_session.send_message(f"{prompt_base}\n{mensagem}")
        return resposta.text
    except Exception as error:
        return f"Desculpe, ocorreu um erro de comunicação: {error}"

def adicionarTarefa(mensagem: str) -> str:
    # Colunas: Número (autoincremento), Classificação, Categoria, Fase, Condição, Nome, Duração, Como fazer, Documentos

    # Dicionário para armazenar os dados da tarefa
    dados = {
        'nome': None, # Nome da tarefa
        'classificacao': None, # Classificação da tarefa
        'categoria': None, # Categoria da tarefa
        'fase': None, # Fase da tarefa
        'condicao': None, # Condição da tarefa
        'duracao': None, # Duração da tarefa
        'documentos': None, # Documentos relacionados
    }

    # Usa a biblioteca 'Regular Expression' para extrair as informações
    # Busca padrões na mensagem
    classificacao_pattern = r"(classificação[:\-]?\s*(.*?)(?=\s*(categoria|fase|condição|duração|como fazer|documentos|$)))" # Classificação após "Classificação:" ou "Classificação-"
    categoria_pattern = r"(categoria[:\-]?\s*(.*?)(?=\s*(classificação|fase|condição|duração|como fazer|documentos|$)))" # Categoria após "Categoria:" ou "Categoria-"
    fase_pattern = r"(fase[:\-]?\s*(.*?)(?=\s*(classificação|categoria|condição|duração|como fazer|documentos|$)))" # Fase após "Fase:" ou "Fase-"
    condicao_pattern = r"(condição[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|duração|como fazer|documentos|$)))" # Condição após "Condição:" ou "Condição-"
    duracao_pattern = r"(\d+\s*(dias|dia|semanas|semana|meses|mês|anos|ano))" # Duração no formato "X dias", "Y semanas", etc.
    documentos_pattern = r"([a-zA-Z0-9_-]+\.(?:pdf|xlsx|docx|txt|csv))" # Arquivos com extensões comuns
    tarefa_pattern = r"'(.*?)'" # Nome da tarefa entre aspas simples

    duracao_match = re.search(duracao_pattern, mensagem, re.IGNORECASE) # Ignora maiúsculas/minúsculas
    classificacao_match = re.search(classificacao_pattern, mensagem, re.IGNORECASE)
    categoria_match = re.search(categoria_pattern, mensagem, re.IGNORECASE)
    fase_match = re.search(fase_pattern, mensagem, re.IGNORECASE)
    condicao_match = re.search(condicao_pattern, mensagem, re.IGNORECASE)
    documentos_match = re.findall(documentos_pattern, mensagem, re.IGNORECASE) # Encontra todas as ocorrências
    tarefa_match = re.search(tarefa_pattern, mensagem, re.IGNORECASE) # Tarefa entre aspas simples
    
    # Armazena os dados extraídos no dicionário
    if tarefa_match:
        dados['tarefa'] = tarefa_match.group(1).strip()
    if duracao_match:
        dados['duracao'] = duracao_match.group(1).strip()
    if classificacao_match:
        dados['classificacao'] = classificacao_match.group(2).strip()  
    if categoria_match:
        dados['categoria'] = categoria_match.group(2).strip()
    if fase_match:
        dados['fase'] = fase_match.group(2).strip()
    if condicao_match:
        dados['condicao'] = condicao_match.group(2).strip()
    if documentos_match:
        dados['documentos'] = ', '.join(documentos_match)
    
    tarefa = dados['tarefa']
    duracao = dados['duracao'] if dados['duracao'] else "duração não especificada"
    classificacao = dados['classificacao'] if dados['classificacao'] else "classificação não especificada"
    categoria = dados['categoria'] if dados['categoria'] else "categoria não especificada"
    fase = dados['fase'] if dados['fase'] else "fase não especificada"
    condicao = dados['condicao'] if dados['condicao'] else "condição não especificada"
    documentos = dados['documentos'] if dados['documentos'] else "não especificado"

    if not dados['tarefa'] or not tarefa:
        return "Desculpe, não consegui identificar a tarefa. Por favor, certifique-se de que a tarefa está entre aspas simples."

    # Código para adicionar a tarefa no banco de dados...
    try:
        pass
    except Exception as error:
        return f"Desculpe, ocorreu um erro ao adicionar a tarefa: {error}"

    return f"Tarefa '{tarefa}' adicionada com sucesso! Detalhes:\n- Duração: {duracao}\n- Classificação: {classificacao}\n- Categoria: {categoria}\n- Fase: {fase}\n- Condição: {condicao}\n- Documentos: {documentos}"

if __name__ == '__main__':
    dados = adicionarTarefa("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Desafio_Número_1_Projeto_1_-_Exportado.xlsx")
    print(dados)

    """
    id_file = '7e93132d-e9cd-405a-ab0b-540eec0b6802.xlsx'
    search = 'Estabelecer requisitos de shelf life'
    pesquisar(id_file, search)
    """