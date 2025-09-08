from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
from .db import conn
import datetime
import uuid
import json
import os

"""
    Esse arquivo é responsável por lidar com as requisições para upload, download e delete de arquivos armazenados. Cria identificadores
    únicos para os dados recebidos e víncula ao usuário.
"""

def carregar_metadados(user_id) -> 'Metadados':
    resultados = conn('SELECT', 'METADATA', 
    'auth_user_id', user_id,    # SELECIONA ONDE (WHERE) AUTH_USER_ID = USER_ID
    id_file=None,               # OS ARGS KEY SÃO AS COLUNAS QUE EU QUERO
    original_name=None,
    import_date=None,
    )

    return resultados

def salvar_metadados(file, name, timestamp, user):
    conn('INSERT', 'METADATA', 
    id_file=file, 
    original_name=name, 
    import_date=timestamp, 
    auth_user_id=user)


# Criação do Blueprint/Projeto da aplicação de upload/download de arquivos
file_bp = Blueprint('file_bp', __name__)

# Rota de upload de arquivos
@file_bp.route('/upload', methods=['POST'])
def upload():
    try:
        # O ID servirá para garantir que não haja conflito entre as requisições dos usuários
        user_id = session.get('user_id')
        if not user_id:
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
        original_name = secure_filename(arquivo.filename)
        id_file = f"{uuid.uuid4()}.xlsx"   # Cria um nome único para o arquivo, a fim de evitar duplicidade e conflitos
        # Acessa a configuração da aplicação principal
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        arquivo_caminho = os.path.join(UPLOAD_FOLDER, id_file)

        # Salva o arquivo no diretório
        arquivo.save(arquivo_caminho)

        data = datetime.datetime.now().isoformat()

        # Armazena os metadados do arquivo
        salvar_metadados(id_file, original_name, data, user_id)

        print(f"Arquivo {original_name} salvo com ID único {id_file} para o usuário {user_id}")

        # Por enquanto, retorna o user_id para o frontend
        # pois, não há autenticação de fato
        return jsonify({
            'mensagem': f'Arquivo {original_name} enviado e salvo com sucesso!',
            'arquivo_importado': id_file,
            'user_id': user_id
        }), 200

    except Exception as error:
        print(f"Erro ao fazer upload do arquivo: {error}")
        return jsonify({'mensagem': f"Ocorreu um erro: {error}"}), 500


# Rota de download de arquivos
@file_bp.route('/download/<id_file>', methods=['GET'])
def download(id_file):
    try:
        # Pega o user_id da sessão
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."})

        metadado_arquivo_importado = carregar_metadados(user_id)

        # Verifica se o arquivo existe e se o usuário é o proprietário
        if id_file not in metadado_arquivo_importado:
            return jsonify({'mensagem': 'Arquivo não encontrado.'}), 404        

        metadado_arquivo = metadado_arquivo_importado[id_file]
        if not user_id or user_id != metadado_arquivo['user_id']:
            return jsonify({'mensagem': 'Acesso negado. Você não é o proprietário do arquivo.'}), 403

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


# Rota para solicitar os arquivos do usuário
@file_bp.route('/arquivos_usuario', methods=['GET'])
def arquivos_usuario():
    arquivos = []

    # Pega o user_id do corpo da requisição GET
    user_id = session.get('user_id')

    print(f"Recebendo requisição para 'arquivos_usuario'. User ID na sessão: {user_id}")

    if not user_id:
        return jsonify({'arquivos': arquivos})
    
    metadado_arquivo_importado = carregar_metadados(user_id)
    
    for id_file, meta in metadado_arquivo_importado.items():
        if meta['user_id'] == user_id:
        	arquivos.append({
                'id': id_file, 
                'nome': meta['original_name'], 
                'data': meta['import_date']
            })
    #print(f"Lista de arquivos encontrada para o usuário {user_id}: {arquivos}")

    return jsonify({'arquivos': arquivos})


# Rota para deletar algum arquivo solicitado
@file_bp.route('/delete/<id_file>', methods=['DELETE'])
def delete(id_file):
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        metadado_arquivo_importado = carregar_metadados(user_id)

        if id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404        

        # Verifica se o user_id que está tentando deletar é o mesmo dos metadados do arquivo
        metadados_arquivo = metadado_arquivo_importado[id_file]
        if user_id != metadados_arquivo['user_id']:
            return jsonify({"mensagem": "Acesso negado. Você não é o proprietário do arquivo."})

        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        arquivo_caminho = os.path.join(UPLOAD_FOLDER, id_file)
        
        # Verifica se o arquivo existe no diretório
        if os.path.exists(arquivo_caminho):
            os.remove(arquivo_caminho)  # Deletar o arquivo do diretório
            
            conn('DELETE', 'METADATA', 'id_file', file)  # Deleta os metadados do arquivo

            print(f"Arquivo {id_file} excluído com sucesso.")

            return jsonify({"mensagem": "Arquivo excluído com sucesso."}), 200
        else:
            return jsonify({"mensagem": "Arquivo não encontrado no servidor."}), 404

    except Exception as error:
        print(f"Erro ao deletar o arquivo: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"})