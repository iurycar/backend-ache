from backend.services.db import consultaSQL
from pathlib import Path
import datetime
import pypdf
import json
import re

from .search import search_docs, normalize_url

"""
    Esse arquivo é responsável por adicionar tarefas às planilhas, bem como gerenciar suas informações.
"""

diretorio = Path(__file__).parent
caminho_dados = diretorio / "data"
caminho_termo = caminho_dados / "sinonimos.json"
caminho_labels = caminho_dados / "labels.json"

diretorio = Path(__file__).resolve().parent.parent
caminho_arquivos = diretorio / "backend" / "data"
caminho_arquivos.mkdir(parents=True, exist_ok=True)

def add_task(mensagem: str) -> str:
    """" Função para adicionar uma tarefa a uma planilha de cronograma modular.
    @param mensagem: Mensagem contendo os detalhes da tarefa.
    @return: Mensagem de confirmação ou erro.
    """
    
    # Exemplos de mensagem: 
    # Adicionar a tarefa 'Analisar dados' com duração de 5 dias, classificação embalagem primária, categoria blisters, fase escopo e briefing, condição A, texto 3, projeto 1, link do documento https://drive.google.com/file/d/1DU9mUBnF9Pctt0jr93FeDg1iUBFdIHdY/view
    # Adicionar a tarefa 'Analisar dados' com duração de 5 dias, classificação embalagem primária, categoria blisters, fase escopo e briefing, condição A, texto 3, projeto 1
    # Adicionar a tarefa 'Analisar dados' com dur de 5 dias, class prim, cat blisters, fase escopo, cond A, txt 3, proj 1, link https://drive.google.com/file/d/1DU9mUBnF9Pctt0jr93FeDg1iUBFdIHdY/view

    coluna: str
    id_file: list[str] = []

    # Dicionário para armazenar os dados da tarefa
    dados: dict = {
        'tarefa': None,  # Nome da tarefa
        'classificacao': None,  # Classificação da tarefa
        'categoria': None,  # Categoria da tarefa
        'fase': None,  # Fase da tarefa
        'condicao': None,  # Condição da tarefa
        'duracao': None,  # Duração da tarefa
        'documentos': None,  # Documentos relacionados
        'texto_referencia': None,  # Texto de referência
        'link_pdf': None,  # Link do PDF
    }

    mensagem = normalize_message(mensagem)

    # Usa a biblioteca 'Regular Expression' para extrair as informações
    # Define os padrões na mensagem
    classificacao_pattern   = r"(classificação[:\-]?\s*(.*?)(?=\s*(categoria|fase|condição|duração|texto|link|documentos?|documento|projeto|nome|tarefa|$)))"
    categoria_pattern       = r"(categoria[:\-]?\s*(.*?)(?=\s*(classificação|fase|condição|duração|texto|link|documentos?|documento|projeto|nome|tarefa|$)))"
    fase_pattern            = r"(fase[:\-]?\s*(.*?)(?=\s*(classificação|categoria|condição|duração|texto|link|documentos?|documento|projeto|nome|tarefa|$)))"
    condicao_pattern        = r"(condição[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|duração|texto|link|documentos?|documento|projeto|nome|tarefa|$)))"
    duracao_pattern         = r"(\d+)\s*(dias?|dia|semanas?|sem|meses?|m[eê]s|m)\b"
    
    documentos_pattern = r"[\w\sáàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ-]+(?:\.(?:xlsx|csv))"
    documentos_label_pattern = r"(documentos?[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|condição|duração|texto|link|projeto|nome|tarefa|$)))"

    projeto_pattern = r"projeto[:\-]?\s*([a-zA-Z0-9 _-]+)"
    tarefa_pattern = r"'(.*?)'"  # Nome da tarefa entre aspas simples

    texto_referencia_pattern = r"(?:texto(?:\s+referência)?)[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|condição|duração|documentos?|documento|projeto|nome|tarefa|link|$))"
    link_pdf_pattern = r"(?:link(?:\s+pdf|\s+do\s+documento)?)[:\-]?\s*(https?://\S+)(?=\s*(classificação|categoria|fase|condição|duração|documentos?|documento|projeto|nome|tarefa|texto|$))"

    # Extrai os dados usando regex
    duracao_match            = re.search(duracao_pattern, mensagem, re.IGNORECASE)
    classificacao_match      = re.search(classificacao_pattern, mensagem, re.IGNORECASE)
    categoria_match          = re.search(categoria_pattern, mensagem, re.IGNORECASE)
    fase_match               = re.search(fase_pattern, mensagem, re.IGNORECASE)
    condicao_match           = re.search(condicao_pattern, mensagem, re.IGNORECASE)
    documentos_match_ext     = re.findall(documentos_pattern, mensagem, re.IGNORECASE)
    documentos_label_match   = re.search(documentos_label_pattern, mensagem, re.IGNORECASE)
    projeto_match            = re.search(projeto_pattern, mensagem, re.IGNORECASE)
    tarefa_match             = re.search(tarefa_pattern, mensagem, re.IGNORECASE)
    texto_match              = re.search(texto_referencia_pattern, mensagem, re.IGNORECASE)
    link_pdf_match           = re.search(link_pdf_pattern, mensagem, re.IGNORECASE)

    # Armazena os dados extraídos no dicionário
    if tarefa_match:
        dados['tarefa'] = clean_text(tarefa_match.group(1).strip())

    # Converte a duração para dias
    if duracao_match:
        qtd: int = int(duracao_match.group(1))
        unidade: str = duracao_match.group(2).lower()
        
        if unidade in ['dia', 'dias']:
            dias = qtd
        elif unidade in ['semana', 'semanas']:
            dias = qtd * 7
        elif unidade in ['mês', 'meses']:
            dias = qtd * 30
        
        dados['duracao'] = f"{dias} dias"
    else:
        return "Desculpe, não consegui identificar a duração da tarefa. Por favor, especifique a duração em dias (ex: '5 dias')."
    
    if classificacao_match:
        bruto = clean_text(classificacao_match.group(2).strip())
        dados['classificacao'] = map_labels(bruto)

    if categoria_match:
        bruto = clean_text(categoria_match.group(2).strip())
        dados['categoria'] = map_labels(bruto)

    if fase_match:
        bruto = clean_text(fase_match.group(2).strip().rstrip('.'))
        dados['fase'] = map_labels(bruto)

    if condicao_match:
        bruto = clean_text(condicao_match.group(2).strip())
        
        primeiro = re.split(r'[\s,;]+', bruto, maxsplit=1)[0].strip().upper()
        primeiro = re.sub(r'[^\wÀ-ÿ]', '', primeiro)

        if primeiro in ['SEMPRE', 'A', 'B', 'C']:
            dados['condicao'] = primeiro
        else:
            dados['condicao'] = bruto

    if texto_match:
        dados['texto_referencia'] = clean_text(texto_match.group(1).strip())
    
    if link_pdf_match:
        dados['link_pdf'] = link_pdf_match.group(1).strip()

    print(f"\nDocumentos encontrados na mensagem: {documentos_match_ext}")

    # Verifica se algum documento ou projeto que foi mencionado existe no banco de dados
    if documentos_match_ext:
        # Se um documento for mencionado, consulta o banco de dados pelo nome do documento
        doc_name: str = documentos_match_ext[0].strip()
        doc_name: str = doc_name.replace(" ", "_") # Substitui espaços em brancos por underline
        doc_metadata: dict = consultaSQL(
            "SELECT", "PROJECTS", 
            where={"original_name": doc_name}, 
            colunas_dados={"id_file": None}
        )

        print(f"Documento mencionado: {doc_name.strip()} -> Metadado: {doc_metadata}")

        if doc_metadata:
            dados['documentos'] = doc_name
            coluna = 'original_name'
            id_file = list(doc_metadata.keys())

    elif projeto_match:
        # Se um projeto for mencionado, consulta o banco de dados pelo nome do projeto
        project_name: str = projeto_match.group(1).strip()
        project_metadata: dict = consultaSQL(
            "SELECT", "PROJECTS", 
            where={"project_name": project_name}, 
            colunas_dados={"id_file": None}
        )

        print(f"Projeto mencionado: {project_name} -> Metadado: {project_metadata}")

        if project_metadata:
            dados['documentos'] = project_name
            coluna = 'project_name'
            id_file = list(project_metadata.keys())
    
    elif documentos_label_match:
        valor_doc: str = documentos_label_match.group(2).strip()

        if re.search(r'\.(xlsx|csv)\b', valor_doc, re.IGNORECASE):
            doc_name: str = valor_doc.replace(" ", "_")
            doc_metadata: dict = consultaSQL(
                "SELECT", "PROJECTS", 
                where={"original_name": doc_name}, 
                colunas_dados={"id_file": None}
            )

            if doc_metadata:
                dados['documentos'] = doc_name
                coluna = 'original_name'
                id_file = list(doc_metadata.keys())
        else:
            project_name: str = valor_doc
            project_metadata: dict = consultaSQL(
                "SELECT", "PROJECTS", 
                where={"project_name": project_name}, 
                colunas_dados={"id_file": None}
            )

            if project_metadata:
                dados['documentos'] = project_name
                coluna = 'project_name'
                id_file = list(project_metadata.keys())
    else:
        dados['documentos'] = None

    # Se não encontrar o link do PDF, tenta buscar no banco de dados o link associado ao id_file
    if not dados['link_pdf']:
        links: list[dict] = consultaSQL(
            "SELECT", "SHEETS",
            where={'id_file': id_file[0]},
            colunas_dados={'reference': None}
        )

        if links and 'reference' in links[0]:
            dados['link_pdf'] = links[0]['reference']
        else:
            dados['link_pdf'] = None

    tarefa = dados['tarefa']
    duracao = dados['duracao']
    classificacao = dados['classificacao']  if dados['classificacao'] else "Definir classificação"
    categoria = dados['categoria']          if dados['categoria'] else "não especificada"
    fase = dados['fase']                    if dados['fase'] else "não especificada"
    condicao = dados['condicao']            if dados['condicao'] else "Indefinido"
    documentos = dados['documentos']

    if not dados['tarefa'] or not tarefa:
        return "Desculpe, não consegui identificar a tarefa. Por favor, certifique-se de que a tarefa está entre aspas simples."

    if not documentos:
        return "Desculpe, não consegui encontrar o documento ou projeto mencionado no banco de dados. Por favor, verifique o nome e tente novamente. 🙁"
    
    if dados['texto_referencia']:
        value = dados['texto_referencia'].strip()
        match_txt = re.search(r'(\d+)', value)

        if match_txt:
            texto_field = f"Texto.{match_txt.group(1)}"
        else:
            if value:
                texto_field = value[0].upper() + value[1:]
            else:
                texto_field = f"Texto.{num}"
    else:
        texto_field = f"Texto.{num}"

    if dados['link_pdf']:
        link_pdf = dados['link_pdf']
    else:
        link_pdf = f"Doc.{num}"

    # Código para adicionar a tarefa no banco de dados...
    try:
        print(f"\nID do arquivo/projeto encontrado: {id_file}")
        #print(f"Coluna usada na busca: {coluna}")
        #print(f"Dados extraídos: {dados}\n")
        if len(id_file) == 1:
            # Gera o próximo número da tarefa (num) automaticamente
            old_num = consultaSQL(
                "SELECT", "SHEETS", 
                where={"id_file": id_file[0]},
                campo={'MAX': 'num'}
            )
            base = 0
            if old_num and old_num[0].get('MAX(num)') is not None:
                base = int(old_num[0]['MAX(num)'])
            num = base + 1

            # Insere a nova tarefa na tabela SHEETS
            consultaSQL(
                "INSERT", "SHEETS", 
                colunas_dados={
                    "id_file": id_file[0],
                    "num": num,
                    "classe": classificacao.replace(".", ""),
                    "category": categoria.replace(".", "").strip().capitalize(),
                    "phase": fase,
                    "status": condicao.replace(".", "").strip().lower().capitalize(),
                    "name": tarefa.capitalize(),
                    "duration": duracao.replace(' dias', ''),
                    "text": texto_field,
                    "reference": link_pdf,
                    "conclusion": 0
                }
            )

            print(f"Tarefa '{tarefa}' número '{num}' adicionada com sucesso! Detalhes:\n- Duração: {duracao}\n- Classificação: {classificacao.replace('.', '')}\n- Categoria: {categoria.replace('.', '').strip().capitalize()}\n- Fase: {fase}\n- Condição: {condicao.replace('.', '').strip().lower().capitalize()}\n- Texto: {texto_field}\n- Documentos: {documentos}\n- Link do PDF: {link_pdf}\n")
        else:
            print("Mais de um arquivo encontrado, tarefa não adicionada.")
            return "Desculpe, mais de um arquivo/projeto encontrado, tarefa não adicionada."

    except Exception as error:
       print(f"Desculpe, ocorreu um erro ao adicionar a tarefa: {error}")
       return f"Desculpe, ocorreu um erro ao adicionar a tarefa"

    return f"Tarefa '{tarefa}' adicionada com sucesso!\n\n-> Detalhes:\n• Duração: {duracao}\n• Classificação: {classificacao}\n• Categoria: {categoria}\n• Fase: {fase}\n• Condição: {condicao}\n• Texto: {texto_field}\n• Projeto/Documento: {documentos}\n• Link do PDF: {link_pdf[8:25]}..."


def normalize_message(mensagem: str) -> str:
    """ Substitui sinonimos por termos padrões para simplificar o regex """
    mensagem = mensagem.lower().strip()

    # Protege o conteúdo entre aspas simples para não ser alterado
    placeholders: dict[str, str] = {}
    def _stash(match):
        chave = f"__Q{len(placeholders)}__" # Gera uma chave única
        placeholders[chave] = match.group(0) # Protege o conteúdo entre aspas simples
        return chave
    mensagem_protegida: str = re.sub(r"'[^']*'", _stash, mensagem)

    print(f"Mensagem original: {mensagem}")
    print(f"Placeholders: {placeholders}")
    print(f"Mensagem protegida: {mensagem_protegida}")

    with open(caminho_termo, "r", encoding="utf-8") as f:
        sinonimos: dict[str, list[str]] = json.load(f)
        #print(f"Sinonimos carregados:\n{sinonimos}")

    # Substitui os sinonimos dos termos pelos termos padrões
    rotulos = {"duração", "classificação", "categoria", "fase", "condição", "texto", "link", "documentos", "documento", "projeto"}
    for termo_padrao, sinonimos_termo in sinonimos.items():
        label: str = termo_padrao.lower().strip()
        
        if label not in rotulos:
            continue
        for sinonimo in sinonimos_termo:
            txt: str = sinonimo.lower().strip()
            pattern: str = rf"\b{re.escape(txt)}\.?\b"
            mensagem_protegida = re.sub(pattern, label, mensagem_protegida, flags=re.IGNORECASE)

    # Restaura o conteúdo protegido entre aspas simples
    for chave, txt in placeholders.items():
        mensagem_protegida = mensagem_protegida.replace(chave, txt)

    return re.sub(r'\s+', ' ', mensagem_protegida).strip()  # Remove espaços extras


def map_labels(valor: str) -> str:
    """ Mapeia valores para rótulos padrão usando um dicionário de labels
     Substitui valores por labels padrões para simplificar o regex """
    valor = valor.lower().strip()

    with open(caminho_labels, "r", encoding="utf-8") as f:
        labels: dict[str, list[str]] = json.load(f)
        #print(f"Labels carregados:\n{labels}")

    for labels_padrao, variantes_label in labels.items():
        for value in variantes_label:
            if valor == value.lower().strip():
                return labels_padrao 
    
    return valor.capitalize()  # Retorna o valor original se não encontrar correspondência


def clean_text(string: str) -> str:
    """ Limpa a string removendo espaços extras e pontuação desnecessária """
    string = string.strip()  # Remove espaços em branco no início e no fim
    string = re.sub(r'\s+', ' ', string)  # Substitui múltiplos espaços por um único espaço
    string = re.sub(r'^\s*[:.\-–—]*\s*', '', string) # Remove prefixos como ":", "-", "--" e "---"
    string = re.sub(r'[\s,.;:]+$', '', string) # Remove pontuação no final
    return string.strip()

""" Funções para lidar com informações das tarefas, como listar tarefas e fornecer instruções. """

def my_tasks(mensagem, usuario) -> str:
    # Selecionar as tarefas do usuário
    # Filtrar as tarefas em que o prazo é curto (3 dias ou menos)
    # Filtrar por condição ('Sempre', 'A', 'B' e 'C')
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
        tarefa['condicao'] = tarefa.get('status', 'Desconhecida')

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
            tarefa['prioridade'] = 'ALTA'
        else:
            tarefa['prazo'] = f'Faltam {dias} dias'

            if dias <=3:
                tarefa['prioridade'] = 'Alta'
            elif (dias > 3 and dias <=7):
                if tarefa['condicao'] in ['Sempre', 'A']:
                    tarefa['prioridade'] = 'Alta'
                else:
                    tarefa['prioridade'] = 'Média'
            elif (dias > 7 and dias <= 10):
                if tarefa['condicao'] in ['Sempre', 'A']:
                    tarefa['prioridade'] = 'Média'
                else:
                    tarefa['prioridade'] = 'Baixa'
            else:
                tarefa['prioridade'] = 'Baixa'

        resposta += f"-> {tarefa['nome']} do projeto {tarefa['project_name']} \n({tarefa['prazo']} | Prioridade: {tarefa['prioridade']} | Condição: {tarefa['condicao']})\n"
        resposta += "--------------------------\n\n"

    #print('Resposta gerada:', resposta)

    return resposta


def how_to_do(mensagem: str, usuario: str, local: bool = False) -> str:
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
            return f"Desculpe, não consegui encontrar as instruções para a tarefa '{task}'."
    else:
        return f"Desculpe, não consegui encontrar as instruções para a tarefa '{task}'."

    link: list[dict] = consultaSQL(
        'SELECT', 'SHEETS',
        where={'num': task, 'project_name': proj},
        campo={'JOIN ON': ['PROJECTS', 'id_file']},
        colunas_dados={
            'reference': None
        }
    )

    if link:
        pdf_link = link[0]['reference']
    else:
        return f"Desculpe, não consegui encontrar o link do documento para a tarefa {task}."

    if not pdf_link.startswith('http'):
        return f"Desculpe, o hyperlink do documento referência para a tarefa '{task}' do projeto '{proj}' é inválido. 😓"

    # Buscar se existe o arquivo .txt ou .pdf correspondente ao PDF na pasta de dados
    arquivo_txt = caminho_arquivos / f"{normalize_url(pdf_link)}.txt"
    arquivo_pdf = caminho_arquivos / f"{normalize_url(pdf_link)}.pdf"

    if not arquivo_txt.exists() and not arquivo_pdf.exists():
        # Adicionar essa mensagem no começo da resposta
        resposta = f"Desculpe a demora, eu não tinha o arquivo em memória. 💾 Para facilitar as próximas consulta do projeto '{proj}', eu já processei o PDF e extraí o texto. 📝\n\n"
        resposta += f"Para fazer a tarefa '{task}' do projeto '{proj}', siga as instruções abaixo:\n\n"

        search_docs(pdf_link)
    
    if arquivo_pdf.exists():
        with pypdf.PdfReader(str(arquivo_pdf)) as pdf:
            texto_extraido = ""
            
            for pagina in pdf.pages:
                texto_extraido += (pagina.extract_text() or "") + "\n"

    elif arquivo_txt.exists():
        # Se o arquivo .txt existir, ler o conteúdo
        with open(arquivo_txt, "r", encoding="utf-8") as f:
            texto_extraido = f.read()
    else:
        return f"Desculpe, não consegui encontrar o arquivo do documento para a tarefa '{task}'."

    # Processar o texto extraído para encontrar as instruções
    match_ref = re.search(r'texto\.?\s*(\d+)', texto_ref, flags=re.IGNORECASE)
    
    if not match_ref:
        return f"Desculpe, o texto de referência '{texto_ref}' é inválido."
    ref_num = match_ref.group(1)

    texto_pattern = rf"(?is)\btexto\.?\s*{ref_num}\s*[:.]?\s*(.*?)(?=\btexto\.?\s*\d+\s*[:.]?|\Z)"
    match = re.search(texto_pattern, texto_extraido)

    if match:
        instrucoes = match.group(1).strip().lower().replace('\n', ' ').split('.')
    else:
        return f"Desculpe, não consegui encontrar as instruções para a tarefa '{task}' no documento."

    #print('Instruções encontradas:', instrucoes)

    for instrucao in instrucoes:
        if instrucao.strip() in ['.', '', ' ']:
            continue
        
        resposta += f"• {instrucao.strip().capitalize()}.\n"

    return resposta


if __name__ == "__main__":
    pass