from flask import Flask, request, jsonify, session, send_from_directory
from chatbotV8.interpretador import interpretar
#from chatbotV8.chatbot import chatbot_bp
from dotenv import load_dotenv
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
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
# Habilita o CORS com suporte a credenciais (cookies) para permitir requesições do REACT
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://127.0.0.1:5173'])   

# Registra o Blueprint
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(file_bp, url_prefix='/')
#app.register_blueprint(chatbot_bp, url_prefix='/')

# Configura o diretório para armazenar os arquivos importados
diretorio = Path(__file__).parent
upload_pasta = diretorio / "dados" / "uploads"
UPLOAD_FOLDER = upload_pasta                    # Diretório da pasta que armazena os arquivos
if not os.path.exists(UPLOAD_FOLDER):           # Verifica se existe a pasta, se não cria ela
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Adiciona a API Key do Gemini, usuário, senha e host do banco de dados nas configurações do Flask
#app.config['GOOGLE_API_KEY'] = os.environ.get("GOOGLE_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Recebe a mensagem do JSON enviado pelo React
        dado = request.json

        if not dado or 'mensagem' not in dado:
            return jsonify({'resposta': 'Por favor, forneça uma mensagem na requisição'})

        mensagem = dado.get('mensagem', '')
        usuario = session.get('user_name', 'Convidado')
        modo_chat = session.get('modo_chat', 'standard')

        #print(f"Modo da sessão ATUAL: '{modo_chat}'")

        # Envia a mensagem e o modo do chat para o interpretador
        resposta_chatbot, proximo_modo_chat = interpretar(mensagem, usuario, modo_chat)

        #print(f"Próximo modo retornado: '{proximo_modo_chat}'")

        # O modo de chat da sessão é atualizado para a próxima interação
        session['modo_chat'] = proximo_modo_chat
        session.modified = True
        print(f"Modo da sessão SALVO: '{session['modo_chat']}'\n")

        return jsonify({'resposta': resposta_chatbot, 'modo_chat': proximo_modo_chat})

    except Exception as error:
        print(f"Erro na requisição: {error}")
        return jsonify({'resposta': 'Ocorreu um erro no servidor. Tente novamente mais tarde.'})

if __name__ == "__main__":
    app.run(debug=True)