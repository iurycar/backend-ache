from backend.db import consultaSQL
from pathlib import Path
import json
import re

"""
    Módulo para adicionar tarefas a planilhas de cronogramas modulares.
"""

diretorio = Path(__file__).parent
caminho_dados = diretorio / "dados"
caminho_termo = caminho_dados / "sinonimos.json"
caminho_labels = caminho_dados / "labels.json"

def add_task(mensagem: str) -> str:
    """" Função para adicionar uma tarefa a uma planilha de cronograma modular.
    @param mensagem: Mensagem contendo os detalhes da tarefa.
    @return: Mensagem de confirmação ou erro.
    """
    
    # Adicionar alguma maneira de autenticação

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

    mensagem = normalize_message(mensagem)

    # Usa a biblioteca 'Regular Expression' para extrair as informações
    # Define os padrões na mensagem
    classificacao_pattern   = r"(classificação[:\-]?\s*(.*?)(?=\s*(categoria|fase|condição|duração|documentos?|documento|projeto|nome|tarefa|$)))"
    categoria_pattern       = r"(categoria[:\-]?\s*(.*?)(?=\s*(classificação|fase|condição|duração|documentos?|documento|projeto|nome|tarefa|$)))"
    fase_pattern            = r"(fase[:\-]?\s*(.*?)(?=\s*(classificação|categoria|condição|duração|documentos?|documento|projeto|nome|tarefa|$)))"
    condicao_pattern        = r"(condição[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|duração|documentos?|documento|projeto|nome|tarefa|$)))"
    duracao_pattern         = r"(\d+)\s*(dias?|dia|semanas?|sem|meses?|m[eê]s|m)\b"
    
    documentos_pattern = r"[\w\sáàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ-]+(?:\.(?:xlsx|csv))"
    documentos_label_pattern = r"(documentos?[:\-]?\s*(.*?)(?=\s*(classificação|categoria|fase|condição|duração|projeto|nome|tarefa|$)))"

    projeto_pattern = r"projeto[:\-]?\s*([a-zA-Z0-9 _-]+)"
    tarefa_pattern = r"'(.*?)'"  # Nome da tarefa entre aspas simples

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
        primeiro = bruto.split()[0].strip().upper()
        if primeiro in ['SEMPRE', 'A', 'B', 'C']:
            dados['condicao'] = primeiro
        else:
            dados['condicao'] = bruto

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

    tarefa = dados['tarefa']
    duracao = dados['duracao']
    classificacao = dados['classificacao']  if dados['classificacao'] else "não especificada"
    categoria = dados['categoria']          if dados['categoria'] else "não especificada"
    fase = dados['fase']                    if dados['fase'] else "não especificada"
    condicao = dados['condicao']            if dados['condicao'] else "não especificada"
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
                    "text": "Texto."+str(num),
                    "reference": "Doc."+str(num),
                    "conclusion": 0
                }
            )

            print(f"Tarefa '{tarefa}' número '{num}' adicionada com sucesso! Detalhes:\n- Duração: {duracao}\n- Classificação: {classificacao.replace('.', '')}\n- Categoria: {categoria.replace('.', '').strip().capitalize()}\n- Fase: {fase}\n- Condição: {condicao.replace('.', '').strip().lower().capitalize()}\n- Documentos: {documentos}")
        else:
            print("Mais de um arquivo encontrado, tarefa não adicionada.")
            return "Desculpe, mais de um arquivo/projeto encontrado, tarefa não adicionada."

    except Exception as error:
       print(f"Desculpe, ocorreu um erro ao adicionar a tarefa: {error}")
       return f"Desculpe, ocorreu um erro ao adicionar a tarefa"

    return f"Tarefa '{tarefa}' adicionada com sucesso! Detalhes:\n- Duração: {duracao}\n- Classificação: {classificacao}\n- Categoria: {categoria}\n- Fase: {fase}\n- Condição: {condicao}\n- Documentos: {documentos}"


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
    rotulos = {"duração", "classificação", "categoria", "fase", "condição", "documentos", "documento", "projeto"}
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

if __name__ == "__main__":
    pass