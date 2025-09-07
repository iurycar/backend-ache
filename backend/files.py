from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import datetime
import uuid
import json
import os

"""
    Esse arquivo é responsável por lidar com as requisições para upload, download e delete de arquivos armazenados. Cria identificadores
    únicos para os dados recebidos e víncula ao usuário.
"""

# ======= ISSO DAQUI PROVAVELMENTE VAI MUDAR =======
# Esse trecho lida com os metadados dos arquivos
# Precisamos criar uma tabela no banco de dados 
# para controlar esses dados de forma mais confiável

# Configura o diretório para o arquivo de metadados
diretorio = Path(__file__).parent
METADATA_FILE = diretorio / "dados" / "metadados.json"
if not os.path.exists(diretorio / "dados"):
    os.makedirs(diretorio / "dados")

def carregar_metadados() -> 'Metadados':
    # Carrega os metadados do arquivo JSON se ele existir.
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_metadados(dado):
    # Salva os metadados no arquivo JSON.
    with open(METADATA_FILE, 'w') as f:
        json.dump(dado, f, indent=4)

# Dicionário para armazenar metadados dos arquivos
metadado_arquivo_importado = carregar_metadados()
# ===================================================

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
        arquivo_nome = secure_filename(arquivo.filename)
        nome_unico = f"{uuid.uuid4()}_{arquivo_nome}"   # Cria um nome único para o arquivo, a fim de evitar duplicidade e conflitos
        # Acessa a configuração da aplicação principal
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        arquivo_caminho = os.path.join(UPLOAD_FOLDER, nome_unico)

        # Salva o arquivo no diretório
        arquivo.save(arquivo_caminho)

        # Armazena os metadados do arquivo
        metadado_arquivo_importado[nome_unico] = {
            'nome_original': arquivo_nome,                          # Armazena o nome original
            'data_importado': datetime.datetime.now().isoformat(),  # Data de importação
            'user_id': user_id                                      # E quem importou
        }
        salvar_metadados(metadado_arquivo_importado)

        print(f"Arquivo {arquivo_nome} salvo com ID único {nome_unico} para o usuário {user_id}")

        # Por enquanto, retorna o user_id para o frontend
        # pois, não há autenticação de fato
        return jsonify({
            'mensagem': f'Arquivo {arquivo_nome} enviado e salvo com sucesso!',
            'arquivo_importado': nome_unico,
            'user_id': user_id
        }), 200

    except Exception as error:
        print(f"Erro ao fazer upload do arquivo: {error}")
        return jsonify({'mensagem': f"Ocorreu um erro: {error}"}), 500


# Rota de download de arquivos
@file_bp.route('/download/<arquivo_importado_id>', methods=['GET'])
def download(arquivo_importado_id):
    try:
        # Pega o user_id da sessão
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."})

        # Verifica se o arquivo existe e se o usuário é o proprietário
        if arquivo_importado_id not in metadado_arquivo_importado:
            return jsonify({'mensagem': 'Arquivo não encontrado.'}), 404
        
        metadado_arquivo = metadado_arquivo_importado[arquivo_importado_id]
        if not user_id or user_id != metadado_arquivo['user_id']:
            return jsonify({'mensagem': 'Acesso negado. Você não é o proprietário do arquivo.'}), 403

        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        # Retorna o arquivo com nome original
        return send_from_directory(
            UPLOAD_FOLDER,
            arquivo_importado_id,
            as_attachment=True,
            download_name=metadado_arquivo['nome_original']
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
    
    for arquivo_id, meta in metadado_arquivo_importado.items():
        if meta['user_id'] == user_id:
        	arquivos.append({
                'id': arquivo_id, 
                'nome': meta['nome_original'], 
                'data': meta['data_importado']
            })

    print(f"Lista de arquivos encontrada para o usuário {user_id}: {arquivos}")

    return jsonify({'arquivos': arquivos})


# Rota para deletar algum arquivo solicitado
@file_bp.route('/delete/<arquivo_id>', methods=['DELETE'])
def delete(arquivo_id):
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        if arquivo_id not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se o user_id que está tentando deletar é o mesmo dos metadados do arquivo
        metadados_arquivo = metadado_arquivo_importado[arquivo_id]
        if user_id != metadados_arquivo['user_id']:
            return jsonify({"mensagem": "Acesso negado. Você não é o proprietário do arquivo."})

        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        arquivo_caminho = os.path.join(UPLOAD_FOLDER, arquivo_id)
        
        # Verifica se o arquivo existe no diretório
        if os.path.exists(arquivo_caminho):
            os.remove(arquivo_caminho)  # Deletar o arquivo do diretório
            
            del metadado_arquivo_importado[arquivo_id]  # Deleta os metadados do arquivo
            salvar_metadados(metadado_arquivo_importado)

            print(f"Arquivo {arquivo_id} excluído com sucesso.")

            return jsonify({"mensagem": "Arquivo excluído com sucesso."}), 200
        else:
            return jsonify({"mensagem": "Arquivo não encontrado no servidor."}), 404

    except Exception as error:
        print(f"Erro ao deletar o arquivo: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"})