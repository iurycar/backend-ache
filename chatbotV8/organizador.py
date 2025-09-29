#from backend.from_to_mysql import from_mysql_extrair
import google.generativeai as genai
from backend.db import consultaSQL
from pathlib import Path
import pandas as pd
import re
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
    coluna: str
    id_file: list[str] = []

    # Dicionário para armazenar os dados da tarefa
    dados: dict = {
        'nome': None,  # Nome da tarefa
        'classificacao': None,  # Classificação da tarefa
        'categoria': None,  # Categoria da tarefa
        'fase': None,  # Fase da tarefa
        'condicao': None,  # Condição da tarefa
        'duracao': None,  # Duração da tarefa
        'documentos': None,  # Documentos relacionados
    }

    # Usa a biblioteca 'Regular Expression' para extrair as informações
    # Busca padrões na mensagem
    classificacao_pattern = r"(classificação[:\-]?\s*(.*?)(?=\s*(categoria|fase|condição|duração|como fazer|documentos|$)))"
    categoria_pattern = r"(categoria[:\-]?\s*(.*?)(?=\s*(classificação|fase|condição|duração|como fazer|documentos|$)))"
    fase_pattern = r"(fase[:\-]?\s*(.*?)(?=\s*(classificação|categoria|condição|duração|como fazer|documentos|$)))"
    condicao_pattern = r"(condição[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|duração|como fazer|documentos|$)))"
    duracao_pattern = r"(\d+\s*(dias|dia))"
    documentos_pattern = r"[\w\sáàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ-]+(?:\.(?:xlsx|csv))"
    projeto_pattern = r"projeto[:\-]?\s*([a-zA-Z0-9 _-]+)"
    tarefa_pattern = r"'(.*?)'"  # Nome da tarefa entre aspas simples

    duracao_match = re.search(duracao_pattern, mensagem, re.IGNORECASE)
    classificacao_match = re.search(classificacao_pattern, mensagem, re.IGNORECASE)
    categoria_match = re.search(categoria_pattern, mensagem, re.IGNORECASE)
    fase_match = re.search(fase_pattern, mensagem, re.IGNORECASE)
    condicao_match = re.search(condicao_pattern, mensagem, re.IGNORECASE)
    documentos_match = re.findall(documentos_pattern, mensagem, re.IGNORECASE)
    projeto_match = re.search(projeto_pattern, mensagem, re.IGNORECASE)
    tarefa_match = re.search(tarefa_pattern, mensagem, re.IGNORECASE)

    # Armazena os dados extraídos no dicionário
    if tarefa_match:
        dados['tarefa'] = tarefa_match.group(1).strip()
    if duracao_match:
        dados['duracao'] = duracao_match.group(1).strip()
    else:
        return "Desculpe, não consegui identificar a duração da tarefa. Por favor, especifique a duração em dias (ex: '5 dias')."
    if classificacao_match:
        dados['classificacao'] = classificacao_match.group(2).strip()
    if categoria_match:
        dados['categoria'] = categoria_match.group(2).strip()
    if fase_match:
        dados['fase'] = fase_match.group(2).strip()
    if condicao_match:
        dados['condicao'] = condicao_match.group(2).strip()

    print(f"\nDocumentos encontrados na mensagem: {documentos_match}")

    # Verifica se algum documento ou projeto que foi mencionado existe no banco de dados
    if documentos_match:
        # Se um documento for mencionado, consulta o banco de dados pelo nome do documento
        doc_name = documentos_match[0].strip()
        doc_name = doc_name.replace(" ", "_") # Substitui espaços em brancos por underline
        doc_metadata = consultaSQL("SELECT", "PROJECT", "original_name", doc_name, id_file=None)

        print(f"Documento mencionado: {doc_name.strip()} -> Metadado: {doc_metadata}")

        if doc_metadata:
            dados['documentos'] = doc_name
            coluna = 'original_name'
            id_file = list(doc_metadata.keys())
    elif projeto_match:
        # Se um projeto for mencionado, consulta o banco de dados pelo nome do projeto
        project_name: str = projeto_match.group(1).strip()
        project_metadata: dict = consultaSQL("SELECT", "PROJECT", "project_name", project_name, id_file=None)

        print(f"Projeto mencionado: {project_name} -> Metadado: {project_metadata}")

        if project_metadata:
            dados['documentos'] = project_name
            coluna = 'project_name'
            id_file = list(project_metadata.keys())
    else:
        dados['documentos'] = None

    tarefa = dados['tarefa']
    duracao = dados['duracao'] if dados['duracao'] else "duração não especificada"
    classificacao = dados['classificacao'] if dados['classificacao'] else "classificação não especificada"
    categoria = dados['categoria'] if dados['categoria'] else "categoria não especificada"
    fase = dados['fase'] if dados['fase'] else "fase não especificada"
    condicao = dados['condicao'] if dados['condicao'] else "condição não especificada"
    documentos = dados['documentos']

    if not dados['tarefa'] or not tarefa:
        return "Desculpe, não consegui identificar a tarefa. Por favor, certifique-se de que a tarefa está entre aspas simples."

    if not documentos:
        return "Desculpe, não consegui encontrar o documento ou projeto mencionado no banco de dados. Por favor, verifique o nome e tente novamente. 🙁"

    # Código para adicionar a tarefa no banco de dados...
    try:
        print(f"\nID do arquivo/projeto encontrado: {id_file}")
        #print(f"Coluna usada na busca: {coluna}")
        #print(f"Dados extraídos: {dados}\n")
        if len(id_file) == 1:
            # Gera o próximo número da tarefa (num) automaticamente
            old_num = consultaSQL("SELECT", "SHEET", "id_file", id_file[0], "MAX(num)",)
            num = str(int(old_num[0]['MAX(num)']) + 1)

            # Insere a nova tarefa na tabela SHEET
            consultaSQL("INSERT", "SHEET", 
                id_file = id_file[0],
                num = num,
                classe = classificacao.replace(".", ""),
                category = categoria.replace(".", ""),
                phase = fase.replace(".", ""),
                status = condicao.replace(".", "").strip().upper(),
                name = tarefa,
                duration = duracao,
                text = "Texto."+num,
                reference = "Doc."+num,
                conclusion = 0
            )

            print(f"Tarefa '{tarefa}' número '{num}' adicionada com sucesso! Detalhes:\n- Duração: {duracao}\n- Classificação: {classificacao}\n- Categoria: {categoria}\n- Fase: {fase}\n- Condição: {condicao}\n- Documentos: {documentos}")
        else:
            print("Mais de um arquivo encontrado, tarefa não adicionada.")
            return "Desculpe, mais de um arquivo/projeto encontrado, tarefa não adicionada."

    except Exception as error:
       print(f"Desculpe, ocorreu um erro ao adicionar a tarefa: {error}")
       return f"Desculpe, ocorreu um erro ao adicionar a tarefa"

    return f"Tarefa '{tarefa}' adicionada com sucesso! Detalhes:\n- Duração: {duracao}\n- Classificação: {classificacao}\n- Categoria: {categoria}\n- Fase: {fase}\n- Condição: {condicao}\n- Documentos: {documentos}"

if __name__ == '__main__':
    #dados = adicionarTarefa("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Desafio_Número_1_Projeto_1_-_Exportado.xlsx")
    dados = adicionarTarefa("Por favor, adicione a tarefa 'Definir especificações de barreira e proteção dos blisters' com duração de 1 mês. Classificação: Embalagem Primária. Categoria: Blisters. Fase: 1. Escopo & Briefing. Condição: C. Documentos: Projeto 1")
    print(dados)

    """
    id_file = '7e93132d-e9cd-405a-ab0b-540eec0b6802.xlsx'
    search = 'Estabelecer requisitos de shelf life'
    pesquisar(id_file, search)
    """