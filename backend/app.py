from flask import Flask, request, jsonify, session, send_from_directory
from chatbotV8.chatbot import chatbot_bp
from dotenv import load_dotenv
from datetime import timedelta
from flask_cors import CORS
from .files import file_bp
from .auth import auth_bp
from pathlib import Path
import os

"""
    Esse arquivo é responsável por servir como porta de entrada da aplicação, enquanto os outros lidam com o chatbot, a importação e exportação de arquivos
    para tratamento. ELe gera as rotas pela qual o Frontend pode enviar e receber dados, por meio das blueprints
"""

# Carrega as variáveis de ambiente do arquivo .env
# Questão de segurança para não manter as chave das APIs abertas
load_dotenv()

# Inicializa o FLask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

DEV_INSECURE = os.getenv('DEV_INSECURE_COOKIES', 'false').lower() == 'true'

if DEV_INSECURE:
    # Dev local (http) mesma máquina/host
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    # Produção (https)
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)

frontend_ip = os.environ.get("BACKEND_LAN_IP")
origins=['http://localhost:5173', 'http://127.0.0.1:5173']
if frontend_ip:
    origins.append(f'http://{frontend_ip}:5173')

# Habilita o CORS com suporte a credenciais (cookies) para permitir requesições do REACT
CORS(app, supports_credentials=True, origins=origins)

# Registra o Blueprint
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(file_bp, url_prefix='/')
app.register_blueprint(chatbot_bp, url_prefix='/')

# Configura o diretório para armazenar os arquivos importados
diretorio = Path(__file__).parent
upload_pasta = diretorio / "uploads"
UPLOAD_FOLDER = upload_pasta                    # Diretório da pasta que armazena os arquivos
if not os.path.exists(UPLOAD_FOLDER):           # Verifica se existe a pasta, se não cria ela
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)