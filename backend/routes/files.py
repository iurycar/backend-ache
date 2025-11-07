from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import text
from pathlib import Path
import datetime
import uuid
import json
import re
import os

from backend.services.from_to_mysql import to_mysql_inserir, from_mysql_extrair
from backend.services.progress import calculate_delay, get_progress, rows_list
from backend.services.db import consultaSQL

"""
    Esse arquivo é responsável por lidar com as requisições para upload, download e delete de arquivos armazenados. 
    Cria identificadores únicos para os dados recebidos e víncula ao usuário.
"""

diretorio = Path(__file__).parent.parent

def load_metadata(id_team: str) -> "Dados do projeto":
    """ Carrega os metadados do arquivo do banco de dados. """
    resultados = consultaSQL(
        'SELECT', 'PROJECTS',
        where={'id_team': id_team},
        colunas_dados={
            'id_file': None,
            'original_name': None,
            'import_date': None,
            'project_name': None,
            'id_team': None,
        }
    )
    return resultados

def save_metadata(id_file: str, filename: str, timestamp: str, id_team: str, project_name: str) -> None:
    """ Salva os metadados do arquivo no banco de dados. """
    consultaSQL(
        'INSERT', 'PROJECTS',
        colunas_dados={
            'id_file': id_file,
            'original_name': filename,
            'import_date': timestamp,
            'project_name': project_name,
            'id_team': id_team,
        }
    )

# Criação do Blueprint/Projeto da aplicação de upload/download de arquivos
file_bp = Blueprint('file_bp', __name__)


# Rota de upload de arquivos
@file_bp.route('/upload', methods=['POST'])
def upload_file():
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

        consulta = consultaSQL(
            'SELECT', 'PROJECTS', 
            where={'original_name': original_name, 'id_team': id_team},
            colunas_dados={'id_file': None}
        )

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
        patterns = [r'Projeto\s+([^-_]+)', r'Parte\s+([^-_]+)'] # Padrão regex para capturar o nome do projeto

        for i in range(len(patterns)):
            match = re.search(patterns[i], arquivo.filename) # Procura o padrão no nome do arquivo

            if match:
                project_name = match.group(1).strip()
                break

        if not match:
            # Se não encontrar nenhum padrão, define um nome genérico
            names = consultaSQL(
                'SELECT', 'PROJECTS', 
                where={'id_team': id_team}, 
                colunas_dados={'project_name': None}
            )
            
            # Se não encontrar um nome para o projeto no nome do arquivo, cria um nome genérico baseado na quantidade de projetos do time
            if names:
                project_name = f"{len(names)+1}"
            else:
                project_name = "1"

        consulta = consultaSQL(
            'SELECT', 'PROJECTS', 
            where={'project_name': project_name, 'id_team': id_team},
            colunas_dados={'id_file': None}
        )

        # Se já existir um projeto com o mesmo nome para o mesmo time, adiciona um novo sufixo numérico
        if consulta:
            max_consulta: list[dict] = consultaSQL(
                'SELECT', 'PROJECTS',
                where={'id_team': id_team},
                campo={'MAX': 'project_name'}
            )

            if max_consulta:
                max_name = max_consulta[0].get('MAX(project_name)', '')
                project_name = int(max_name) + 1

        # Armazena os metadados do arquivo
        save_metadata(id_file, original_name, date, id_team, project_name)

        # Verifica se o id_file foi salvo corretamente no banco de dados
        project_metadata = consultaSQL('SELECT', 'PROJECTS', where={'id_file': id_file}, colunas_dados={'id_file': None})
        if not project_metadata:
            print(f"Erro: Metadados do arquivo {id_file} não foram salvos no banco de dados.")
            return jsonify({'mensagem': 'Erro ao salvar os metadados do arquivo.'}), 500

        # Manda os dados da tabela para o MySQL
        to_mysql_inserir(id_file)

        date = datetime.datetime.now().astimezone().isoformat()

        consultaSQL(
            'UPDATE', 'SHEETS',
            where={},
            colunas_dados={'duration': 'SQL:REPLACE(`duration`, " dias", "")'},
        )

        # Atualiza start_date e end_date em lote (normalizando conclusion 0–1 ou 0–100)
        consultaSQL(
            'UPDATE', 'SHEETS', 
            where={'id_file': id_file},
            colunas_dados={'start_date': date},
            where_especial={'start_date': 'IS NULL', 'conclusion': ['> 0', '< 1']}
        )

        consultaSQL(
            'UPDATE', 'SHEETS', 
            where={'id_file': id_file, 'conclusion': 1}, 
            colunas_dados={'end_date': date},
            where_especial={'end_date': 'IS NULL'}
        )

        consultaSQL(
            'UPDATE', 'SHEETS',
            where_especial={'start_date': 'IS NOT NULL', 'deadline': 'IS NULL', 'end_date': 'IS NULL'},
            colunas_dados={'deadline': 'SQL:DATE_ADD(`start_date`, INTERVAL `duration` DAY)'}
        )

        # Garantir que seja substitua todas as ocorrências de " dias" na coluna duration
        consultaSQL(
            'UPDATE', 'SHEETS',
            where={},
            colunas_dados={'duration': 'SQL:REPLACE(`duration`, " dias", "")'},
        )
    
        print(f"Arquivo {original_name} salvo com ID único {id_file} para o usuário {user_id}")

        return jsonify({
            'mensagem': f'Arquivo {original_name} enviado e salvo com sucesso!',
            'arquivo_importado': id_file,
        }), 200

    except Exception as error:
        print(f"Erro ao fazer upload do arquivo: {error}")
        return jsonify({'mensagem': f"Ocorreu um erro."}), 500



# Rota de download de arquivos
@file_bp.route('/download/<id_file>', methods=['GET'])
def download_file(id_file: str):
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
        return jsonify({'mensagem': f"Ocorreu um erro."}), 501



# Rota para deletar algum arquivo solicitado
@file_bp.route('/delete/<id_file>', methods=['DELETE'])
def delete_file(id_file: str):
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

            consultaSQL('DELETE', 'SHEETS', where={'id_file': id_file}) # Deleta todas as linhas com a mesma FK
            consultaSQL('DELETE', 'PROJECTS', where={'id_file': id_file})  # Deleta os metadados do arquivo

            print(f"Arquivo {id_file} excluído com sucesso.")

            return jsonify({"mensagem": "Arquivo excluído com sucesso."}), 200
        else:
            return jsonify({"mensagem": "Arquivo não encontrado no servidor."}), 404

    except Exception as error:
        print(f"Erro ao deletar o arquivo: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500



# Rota para solicitar os arquivos do usuário
@file_bp.route('/arquivos_usuario', methods=['GET'])
def get_team_files():
    arquivos: list[dict] = []

    user_id = session.get('user_id')
    id_team = session.get('user_team')

    print(f"Recebendo requisição para 'get_files'. User ID na sessão: {user_id}")

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
def get_data_sheet(id_file):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        print(f"Recebendo requisição para 'get_data_sheet'. User ID na sessão: {user_id}")
        print(f"ID do time na sessão: {id_team}")

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        colunas = {
            'num': None,
            'classe': None,
            'category': None,
            'phase': None,
            'status': None,
            'name': None,
            'SQL:CONCAT(`duration`, " dias") AS `duration`': None,
            'text': None,
            'reference': None,
            'conclusion': None,
            'start_date': None,
            'deadline': None,
            'end_date': None,
            'user_id': None,
        }

        # Se o 'id_file' for 'null' ou 'all', busca todas as tarefas de todos os arquivos do time
        if id_file is None or id_file.lower() == 'null' or id_file.strip() == 'all':
            data: list[dict] = consultaSQL(
                'SELECT', 'SHEETS',
                where={'id_team': id_team},
                campo={'JOIN ON': ['PROJECTS', 'id_file']},
                colunas_dados=colunas
            )

            if not data:
                return jsonify({"mensagem": "Nenhuma informação de planilha encontrada para o time."}), 404

            for task in data:
                id_user = task.get('user_id')

                if id_user not in (None, '', 'null'):
                    user_info = consultaSQL(
                        'SELECT', 'EMPLOYEES', 
                        where={'user_id': id_user},
                        colunas_dados={
                            'first_name': None,
                            'last_name': None,
                        }
                    )

                    if user_info:
                        task['responsible'] = f"{user_info[0].get('first_name', '')} {user_info[0].get('last_name', '')}".strip()

            data = calculate_delay(data)
            return jsonify({'dados': data}), 200

        else:
            data: list[dict] = consultaSQL(
                'SELECT', 'SHEETS', 
                where={'id_file': id_file},
                colunas_dados=colunas,
            )

        if not data:
            return jsonify({"mensagem": "Informações da planilha não encontrada."}), 404

        date = datetime.datetime.now().astimezone().date()

        for task in data:
            # Adiciona o nome do responsável pela tarefa
            id_user = task.get('user_id')
            if id_user not in (None, '', 'null'):
                user_info = consultaSQL(
                    'SELECT', 'EMPLOYEES', 
                    where={'user_id': id_user},
                    colunas_dados={
                        'first_name': None,
                        'last_name': None,
                    }
                )

                if user_info:
                    task['responsible'] = f"{user_info[0].get('first_name', '')} {user_info[0].get('last_name', '')}".strip()

        completed: list[dict] = consultaSQL(
            'SELECT', 'PROJECTS', 
            where={'id_file': id_file},
            colunas_dados={'completed': None}
        )

        if completed[0].get('completed', 0) == 0:        
            data = calculate_delay(data)

        return jsonify({'dados': data}), 200

    except Exception as error:
        print(f"Erro ao buscar todas as tarefas: {error}"), 500