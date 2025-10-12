from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
from .tasks import calculate_delay, calculate_progress, rows_list
from .from_to_mysql import to_mysql_inserir, from_mysql_extrair
from werkzeug.utils import secure_filename
from .db import consultaSQL
from sqlalchemy import text
from pathlib import Path
import datetime
import uuid
import json
import re
import os

"""
    Esse arquivo é responsável por lidar com as requisições para upload, download e delete de arquivos armazenados. 
    Cria identificadores únicos para os dados recebidos e víncula ao usuário.
"""

diretorio = Path(__file__).parent

def load_metadata(id_team: str) -> "Dados do projeto":
    """ Carrega os metadados do arquivo do banco de dados. """
    resultados = consultaSQL('SELECT', 'PROJECT', 
        'id_team', id_team,         # SELECIONA ONDE (WHERE) ID_TEAM = ID_TEAM
        id_file=None,               # OS ARGS KEY SÃO AS COLUNAS QUE EU QUERO QUE RETORNE
        original_name=None,
        import_date=None,
        project_name=None,
        id_team=None,
    )
    return resultados

def save_metadata(id_file: str, filename: str, timestamp: str, id_team: str, project_name: str) -> None:
    """ Salva os metadados do arquivo no banco de dados. """
    consultaSQL('INSERT', 'PROJECT', 
        id_file=id_file, 
        original_name=filename, 
        import_date=timestamp,
        project_name=project_name, 
        id_team=id_team,
    )

# Criação do Blueprint/Projeto da aplicação de upload/download de arquivos
file_bp = Blueprint('file_bp', __name__)


# Rota de upload de arquivos
@file_bp.route('/upload', methods=['POST'])
def upload():
    try:
        # O ID servirá para garantir que não haja conflito entre as requisições dos usuários
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."})

        # Verifica se tem algum arquivo na requisição
        if 'arquivo' not in request.files:
            return jsonify({'mensagem': 'Nenhum arquivo enviado.'}), 400

        # Pega o arquivo na requisição
        arquivo = request.files['arquivo']

        # Verifica se o arquivo tem nome
        if arquivo.filename == '':
            return({'mensagem': 'Nenhum arquivo selecionado.'}), 400

        # Verifica o formato do arquivo é um tipo do Excel
        if not arquivo.filename.endswith(('.xlsx', '.csv')):
            return({'mensagem': 'Formato do arquivo incompatível.'}), 400

        # Torna o nome do arquivo seguro e o armazena
        original_name: str = secure_filename(arquivo.filename)

        consulta = consultaSQL('SELECT', 'PROJECT', 'original_name', original_name, 'id_team', id_team, id_file=None)

        # Se já existir um arquivo com o mesmo nome para o mesmo time, adiciona um sufixo numérico
        if consulta:
            split: list[str] = original_name.rsplit('.', 1)
            name: str = split[0]
            ext: str = split[1] if len(split) > 1 else ''

            original_name = f"{name}_v{len(consulta)+1}.{ext}"  # Adiciona o sufixo e a extensão de volta

        # Gera um ID único para o arquivo
        id_file = f"{uuid.uuid4()}.xlsx"   # Cria um nome único para o arquivo, a fim de evitar duplicidade e conflitos
        # Acessa a configuração da aplicação principal
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        arquivo_caminho = os.path.join(UPLOAD_FOLDER, id_file)

        # Salva o arquivo no diretório
        arquivo.save(arquivo_caminho)

        # Pega a data e horário
        date = datetime.datetime.now().astimezone().isoformat()

        # Exemplo nome do projeto 'Projeto 1' em "Desafio Número 1_Projeto 1 - Exportado.xlsx"
        project_name_pattern = r'Projeto\s+([^-_]+)'  # Padrão regex para capturar o nome do projeto
        match = re.search(project_name_pattern, arquivo.filename) # Procura o padrão no nome do arquivo
        parte_name_pattern = r'Parte\s+([^-_]+)'
        match2 = re.search(parte_name_pattern, arquivo.filename)

        if match:
            project_name = match.group(1).strip()
        elif match2:
            project_name = match2.group(1).strip()
        elif not match and not match2:
            project_name = "Sem Nome"

        consulta = consultaSQL('SELECT', 'PROJECT', 'project_name', project_name, 'id_team', id_team, id_file=None)

        # Se já existir um projeto com o mesmo nome para o mesmo time, adiciona um sufixo numérico
        if consulta:
            project_name = f"{project_name} ({len(consulta)+1})"

        # Armazena os metadados do arquivo
        save_metadata(id_file, original_name, date, id_team, project_name)

        # Verifica se o id_file foi salvo corretamente no banco de dados
        project_metadata = consultaSQL('SELECT', 'PROJECT', 'id_file', id_file, id_file=None)
        if not project_metadata:
            print(f"Erro: Metadados do arquivo {id_file} não foram salvos no banco de dados.")
            return jsonify({'mensagem': 'Erro ao salvar os metadados do arquivo.'}), 500

        # Manda os dados da tabela para o MySQL
        to_mysql_inserir(id_file)

        # Atualiza start_date e end_date em lote (normalizando conclusion 0–1 ou 0–100)
        consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, conclusion='> 0 AND < 1', start_date='NOW()')
        consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'conclusion', 1, end_date='NOW()')

        #UPDATE `sheet` SET `start_date` = NOW() WHERE (`start_date` IS NULL) AND (`conclusion` > 0 AND `conclusion` < 1) AND `id_file` = :id_file;
    
        print(f"Arquivo {original_name} salvo com ID único {id_file} para o usuário {user_id}")

        return jsonify({
            'mensagem': f'Arquivo {original_name} enviado e salvo com sucesso!',
            'arquivo_importado': id_file,
        }), 200

    except Exception as error:
        print(f"Erro ao fazer upload do arquivo: {error}")
        return jsonify({'mensagem': f"Ocorreu um erro: {error}"}), 500



# Rota de download de arquivos
@file_bp.route('/download/<id_file>', methods=['GET'])
def download(id_file: str):
    try:
        # Pega o user_id da sessão
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."})

        metadado_arquivo_importado = load_metadata(id_team)

        # Verifica se o arquivo existe e se o usuário é o proprietário
        if id_file not in metadado_arquivo_importado:
            return jsonify({'mensagem': 'Arquivo não encontrado.'}), 404        

        # Verifica se o usuário faz parte da equipe proprietária do arquivo
        metadado_arquivo = metadado_arquivo_importado[id_file]
        if id_team != metadado_arquivo['id_team']:
            return jsonify({'mensagem': 'Acesso negado'}), 403

        # Extrai os dados do MySQL e coloca na panilha original 
        from_mysql_extrair(id_file)

        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        # Retorna o arquivo com nome original
        return send_from_directory(
            UPLOAD_FOLDER,
            id_file,
            as_attachment=True,
            download_name=metadado_arquivo['original_name']
        )
    except Exception as error:
        print(f"Erro ao fazer download do arquivo: {error}")
        return jsonify({'mensagem': f"Ocorreu um erro: {error}"}), 501



# Rota para deletar algum arquivo solicitado
@file_bp.route('/delete/<id_file>', methods=['DELETE'])
def delete(id_file: str):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        metadado_arquivo_importado = load_metadata(id_team)

        if id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404        

        # Verifica se o usuário faz parte da equipe proprietária do arquivo
        metadados_arquivo = metadado_arquivo_importado[id_file]
        if id_team != metadados_arquivo['id_team']:
            return jsonify({"mensagem": "Acesso negado. Você não é o proprietário do arquivo."})

        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        arquivo_caminho = os.path.join(UPLOAD_FOLDER, id_file)
        
        # Verifica se o arquivo existe no diretório
        if os.path.exists(arquivo_caminho):
            os.remove(arquivo_caminho)  # Deleta o arquivo do diretório
            
            consultaSQL('DELETE', 'SHEET', 'id_file', id_file) # Deleta todas as linhas com a mesma FK
            consultaSQL('DELETE', 'PROJECT', 'id_file', id_file)  # Deleta os metadados do arquivo

            print(f"Arquivo {id_file} excluído com sucesso.")

            return jsonify({"mensagem": "Arquivo excluído com sucesso."}), 200
        else:
            return jsonify({"mensagem": "Arquivo não encontrado no servidor."}), 404

    except Exception as error:
        print(f"Erro ao deletar o arquivo: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"})



# Rota para solicitar os arquivos do usuário
@file_bp.route('/arquivos_usuario', methods=['GET'])
def arquivos_usuario():
    arquivos: list[dict] = []

    user_id = session.get('user_id')
    id_team = session.get('user_team')

    print(f"Recebendo requisição para 'arquivos_usuario'. User ID na sessão: {user_id}")

    if (not id_team or not user_id) or (id_team is None or user_id is None):
        return jsonify({'arquivos': arquivos})
    
    metadado_arquivo_importado = load_metadata(id_team)

    if not metadado_arquivo_importado:
        print(f"Nenhum arquivo encontrado para o usuário {user_id}.")
        return jsonify({'arquivos': arquivos})
    
    for id_file, meta in metadado_arquivo_importado.items():
        if meta['id_team'] == id_team:
        	arquivos.append({
                'id': id_file, 
                'name': meta['original_name'], 
                'project': "Projeto  " + meta['project_name'],
                'importedAt': meta['import_date']
            })
    #print(f"Lista de arquivos encontrada para o usuário {user_id}: {arquivos}")

    return jsonify({'arquivos': arquivos})



@file_bp.route('/arquivo/<id_file>/dados', methods=['GET'])
def send_data(id_file):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        print(f"Recebendo requisição para 'send_data'. User ID na sessão: {user_id}")
        print(f"ID do time na sessão: {id_team}")

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        data: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file,
            num=None,
            classe=None,
            category=None,
            phase=None,
            status=None,
            name=None,
            duration=None,
            text=None,
            reference=None,
            conclusion=None,
            start_date=None,
            end_date=None,
            responsible=None,
        )

        if not data:
            return jsonify({"mensagem": "Informações da planilha não encontrada."}), 404

        completed: list[dict] = consultaSQL('SELECT', 'PROJECT', 'id_file', id_file, completed=None)

        if completed[0].get('completed', 0) == 0:        
            data = calculate_delay(data)

        return jsonify({'dados': data}), 200

    except Exception as error:
        print(f"Erro ao buscar todas as tarefas: {error}")


# Rota para atualizar/adicionar uma linha da planilha
@file_bp.route('/arquivo/<id_file>/linha/<int:num>', methods=['PATCH'])
def update_add_row(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        data = request.get_json(silent=True) or {} # Dados enviados na requisição

        if 'responsavel' in data and 'responsible' not in data:
            data['responsible'] = data.pop('responsavel')

        # Campos permitidos para atualização
        permitidos = {
            'num', 'classe', 'category', 'phase', 'status',
            'name', 'duration', 'text', 'reference', 'conclusion',
            'responsible'
        }

        # Filtra apenas os campos permitidos
        update_args: dict = {}
        for key, value in data.items():
            if key not in permitidos:
                return jsonify({"mensagem": f"Campo inválido para atualização: {key}"}), 400
            else:
                update_args[key] = value

        # Define valores padrão se campos estiverem ausentes ou vazios
        if update_args.get('status') is None or update_args.get('status') == '':
            update_args['status'] = '??'
        if update_args.get('classe') is None or update_args.get('classe') == '':
            update_args['classe'] = 'INDEFINIDO'
        if update_args.get('name') is None or update_args.get('name') == '':
            update_args['name'] = 'SEM NOME'
        if update_args.get('duration') is None or update_args.get('duration') == '':
            update_args['duration'] = 'INDEFINIDO'
        if update_args.get('phase') is None or update_args.get('phase') == '':
            update_args['phase'] = 'INDEFINIDO'
        if update_args.get('category') is None or update_args.get('category') == '':
            update_args['category'] = 'INDEFINIDO'

        print("Update: ", data)
        print("Update args: ", update_args)

        # Normaliza conclusion (0-1)
        if 'conclusion' in update_args:
            try:
                porcentagem = float(update_args['conclusion'])
                # aceita 0–100 e 0–1; se c>1, converte para 0–1
                if porcentagem <= 1:
                    update_args['conclusion'] = porcentagem
                else:
                    update_args['conclusion'] = min(max(porcentagem / 100, 0), 1)
            except Exception:
                update_args.pop('conclusion', None)

        if not update_args:
            return jsonify({"mensagem": "Nada para atualizar."}), 400
        
        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None
        )

        # Se a linha não existir, insere uma nova linha
        if not linha_existente:
            # calcular próximo número de linha para este arquivo
            try:
                max_result = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'MAX(num)')
                max_num: int = 0
                if isinstance(max_result, list) and max_result:
                    # chave pode ser 'MAX(num)' dependendo do SELECT
                    row = max_result[0]
                    max_num = int(row.get('MAX(num)', 0) or 0) # Se for None, usa 0
            except Exception:
                max_num = 0

            novo_num: int = max_num + 1

            consultaSQL('INSERT', 'SHEET',
                id_file = id_file,
                num = novo_num,
                classe = update_args.get('classe', ''),
                category = update_args.get('category', ''),
                phase = update_args.get('phase', ''),
                status = (update_args.get('status', '') or '').strip().upper(),
                name = update_args.get('name', ''),
                duration = update_args.get('duration', ''),
                text = "Texto."+str(novo_num),
                reference = "Doc."+str(novo_num),
                conclusion = update_args.get('conclusion', 0),
                responsible = update_args.get('responsible', '')
            )

            return jsonify({
                "mensagem": "Linha inserida com sucesso.",
                "inserted": {**update_args, 'num': novo_num}
            }), 201
        else:
            print(f"Atualizando linha {num} do arquivo {id_file} com: {update_args}")

            # Executa o UPDATE na linha alvo (chave: id_file + num atual)
            consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'num', num, **update_args)

        return jsonify({
            "mensagem": "Linha atualizada com sucesso.",
            "updated": update_args
        }), 200

    except Exception as error:
        print(f"Erro ao atualizar linha: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


# Rota para deletar uma linha da planilha
@file_bp.route('/arquivo/<id_file>/linha/<int:num>', methods=['DELETE'])
def delete_row(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        # Executa o DELETE na linha alvo (chave: id_file + num atual)
        consultaSQL('DELETE', 'SHEET', 'id_file', id_file, 'num', num)

        return jsonify({"mensagem": "Linha deletada com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao deletar linha: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


# Rota para iniciar uma tarefa
@file_bp.route('/arquivo/<id_file>/start/<int:num>', methods=['POST'])
def start_task(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')
        user_name = session.get('user_name', 'Usuário')
        user_last_name = session.get('user_last_name', '')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None,
            start_date=None
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        start = linha_existente[0]['start_date']
        if start:
            return jsonify({"mensagem": "A tarefa já está em andamento."}), 400

        date = datetime.datetime.now().astimezone().isoformat()

        responsible_name = user_name + " " + user_last_name

        # Atualiza o status da tarefa para "EM ANDAMENTO"
        consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'num', num, start_date=date, responsible=responsible_name)

        consulta: list[dict] = consultaSQL('SELECT', 'TASK_HISTORY', 'user_id', user_id, "MAX(in_progress)")

        print("Consulta de histórico:", consulta)

        max_in_progress: int = 0
        if isinstance(consulta, list) and consulta:
            row: dict = consulta[0]
            max_in_progress = int(row.get('MAX(in_progress)', 0) or 0)
        max_in_progress += 1

        # Registra o início da tarefa no histórico
        consultaSQL('UPDATE', 'TASK_HISTORY', 'user_id', user_id, in_progress=max_in_progress)

        return jsonify({"mensagem": "Tarefa iniciada com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao iniciar tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


# Rota para desfazer o início de uma tarefa
@file_bp.route('/arquivo/<id_file>/start/<int:num>', methods=['DELETE'])
def undo_start_task(id_file: str, num: int):
    """Remove o start_date (volta tarefa para 'não iniciada' em termos de início)."""
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None,
            conclusion=None,
            start_date=None
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        start = linha_existente[0].get('start_date')
        if not start:
            return jsonify({"mensagem": "A tarefa ainda não foi iniciada."}), 400

        if linha_existente[0].get('conclusion', 0) == 1:
            return jsonify({"mensagem": "A tarefa já foi concluída; não é possível desfazer o início."}), 400

        # Define start_date como NULL
        consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'num', num, start_date=None, conclusion=0)

        return jsonify({"mensagem": "Início da tarefa removido com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao desfazer início de tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


@file_bp.route("/projects/data", methods=['GET'])
def projects_data():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        data: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file,
            duration=None,
            conclusion=None,
            start_date=None,
            end_date=None,
            responsible=None,
        )

    except Exception as error:
        print(f"Erro ao buscar dados dos projetos: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


@file_bp.route("/projects/completed/<id_file>", methods=['GET'])
def project_completed(id_file: str):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        print(f"Recebendo requisição para 'project_completed'. User ID na sessão: {user_id}")

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        consulta: dict = consultaSQL('SELECT', 'PROJECT', 'id_file', id_file, completed=None)
        project_rows = rows_list(consulta)

        if not consulta:
            return jsonify({"mensagem": "Projeto não encontrado."}), 404

        if int(project_rows[0].get('completed', 0)) == 1:
            return jsonify({'mensagem': "O projeto já foi concluído."}), 200

        consulta: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, conclusion=None, num=None)

        for linha in consulta:
            if float(linha.get('conclusion', 0)) < 1:
                return jsonify({'mensagem': f"A tarefa {linha.get('num')} ainda não foi concluída."}), 200
        
        consultaSQL('UPDATE', 'PROJECT', 'id_file', id_file, completed=1)

        consulta: list[dict] = consultaSQL('SELECT', 'TEAMS', 'id_team', id_team, 'MAX(completed_projects)')

        max_completed: int = 0
        if isinstance(consulta, list) and consulta:
            row: dict = consulta[0]
            max_completed = int(row.get('MAX(completed_projects)', 0) or 0) # Se for None, usa 0        
        max_completed += 1

        consultaSQL('UPDATE', 'TEAMS', 'id_team', id_team, completed_projects=max_completed)

        print(f"Projeto {id_file} marcado como concluído.")

        return jsonify({'mensagem': "Projeto marcado como concluído com sucesso."}), 200
    except Exception as error:
        print(f"Erro ao buscar dados dos projetos: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para buscar os funcionários do time
@file_bp.route('/team/employees', methods=['GET'])
def team_employees():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Buscar todos os funcionários do time
        employees: list[dict] = consultaSQL('SELECT', 'EMPLOYEE', 'id_team', id_team, first_name=None, last_name=None)

        valid_employees: list[dict] = []

        # Filtra apenas os funcionários com nome e sobrenome válidos
        for emp in employees:
            complete_name: dict = {}
            first_name: str = emp.get('first_name', '').strip()
            last_name: str = emp.get('last_name', '').strip()

            if first_name and last_name:
                complete_name['name'] = f"{first_name} {last_name}"
            elif first_name:
                complete_name['name'] = first_name

            if complete_name:
                valid_employees.append(complete_name)

        print(f"Funcionários encontrados para o time {id_team}: {valid_employees}")

        return jsonify({'employees': valid_employees}), 200
    except Exception as error:
        print(f"Erro ao buscar funcionários do time: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para buscar dados dos funcionários do time
@file_bp.route('/team/info', methods=['POST'])
def data_team():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        consulta: list[dict] = consultaSQL('SELECT', 'EMPLOYEE', 'id_team', id_team, 
            email=None,
            first_name=None,
            last_name=None,
            role=None,
            cellphone=None,
            active=None
        )

        if not consulta:
            return jsonify({"mensagem": "Nenhum funcionário encontrado para este time."}), 404
        
        # Para cada funcionário, buscar o endereço
        for emp in consulta:
            consulta_address: list[dict] = consultaSQL('SELECT', 'ADDRESS', 'user_id', emp.get('user_id'), 
                city=None, 
                state=None, 
                country=None
            )

            if consulta_address:
                emp['address'] = consulta_address[0]
            else:
                emp['address'] = {}
                emp['address']['city'] = None
                emp['address']['state'] = None
                emp['address']['country'] = None

        return jsonify({'employees': consulta}), 200
    except Exception as error:
        print(f"Erro ao buscar funcionários do time: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para buscar o progresso das tarefas do projeto
@file_bp.route('/project/progress_tasks/<id_file>', methods=['GET'])
def project_progress_tasks(id_file: str):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Retornar progresso = {'total': X, 'concluidas': Y, 'em andamento': Z, 'não iniciadas': W, 'atrasadas': V}
        progresso = {
            'total': 0,
            'concluded': 0,
            'in_progress': 0,
            'not_started': 0,
            'overdue': 0
        }

        # Se id_file for 'all' ou vazio, então pegar o progresso de todos os projetos ativos do time
        all_projects = (not id_file) or (id_file.strip() == '') or (id_file == None) or (id_file.lower() == 'null')

        if all_projects:

            consulta_projetos: list[dict] = consultaSQL('SELECT', 'PROJECT', 'id_team', id_team,
                completed=None,
                id_file=None,
                project_name=None
            )

            # Transforma a lista de dicionários em uma lista simples de dicionários
            project_rows = rows_list(consulta_projetos)

            if not project_rows:
                return jsonify({"mensagem": "Nenhum projeto ativo encontrado para este time."}), 404

            # Para cada projeto, calcular o progresso
            for projeto in project_rows:
                pid = projeto.get('id_file') # Pega o id_file do projeto
                
                if not pid:
                    continue

                # Se o projeto já estiver concluído, então todas as tarefas estão concluídas
                if int(projeto.get('completed', 0) or 0) == 1:
                    consulta_tarefas: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', projeto['id_file'], "COUNT(*)")
                    
                    if consulta_tarefas:
                        total = int(consulta_tarefas[0].get('COUNT(*)', 0) or 0)
                        progresso['total'] += total
                        progresso['concluded'] += total
                    continue

                # Se o projeto não estiver concluído, calcular o progresso normalmente
                progresso = calculate_progress(projeto['id_file'], progresso)

        else: 
            # Se o id_file foi fornecido, então pega o progresso somente daquele projeto
            consulta_projeto: list[dict] = consultaSQL('SELECT', 'PROJECT', 'id_team', id_team, 'id_file', id_file,
                completed=None,
                id_file=None,
                project_name=None
            )

            if not consulta_projeto:
                return jsonify({"mensagem": "Projeto não encontrado para este time."}), 404

            print(f"Projeto ativo encontrado para o time {id_team}: {consulta_projeto}")

            # Se o projeto já estiver concluído, então todas as tarefas estão concluídas
            if int(consulta_projeto[id_file].get('completed', 0)) == 1:
                consulta_tarefas: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, "COUNT(*)")
                
                if consulta_tarefas:
                    progresso['total'] += consulta_tarefas[0].get('COUNT(*)', 0)
                    progresso['concluded'] += consulta_tarefas[0].get('COUNT(*)', 0)
            else:
                progresso = calculate_progress(id_file, progresso)

        return jsonify({"progresso": progresso}), 200
            

    except Exception as error:
        print(f"Erro ao buscar progresso das tarefas do projeto: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500