from flask import Blueprint, request, jsonify, session
from .hashing import checkPassword
from .db import consultaSQL
from pathlib import Path

"""
    Esse arquivo é responsável por criar as rotas e os meios de autenticação
"""

def consulta_db(email: str) -> dict | None:
    resultado = consultaSQL(
        "SELECT", "EMPLOYEES", 
        where={'email': email},
        colunas_dados={
            'user_id': None,
            'password_hash': None,
            'first_name': None,
            'last_name': None,
            'role': None,
            'id_team': None
        }
    )

    return resultado

# Criação do Blueprint/Projeto da aplicação de autenticação
auth_bp = Blueprint('auth_bp', __name__)

# Rota de login
@auth_bp.route("/login", methods=['POST'])
def login():
    dados = request.json

    print(f"Dados recebidos: {dados}")

    email: str = dados.get('email')
    password: str = dados.get('password')

    users_db: dict = consulta_db(email)   # Consulta o banco de dados pelo email

    print(f"\nUsuários encontrados: {users_db}\n")

    if users_db:
        user_dados: dict = users_db[0]   # Verifica se o email existe no banco de dados
        
        print(f"Dados do usuário para {email}: {user_dados}")

        # Verifica se a senha está correta
        same = checkPassword(password, user_dados['password_hash'])

        if user_dados and same:
            session['user_id'] = user_dados['user_id']
            session['user_email'] = email
            session['user_name'] = user_dados['first_name']
            session['user_last_name'] = user_dados['last_name']
            session['user_role'] = user_dados['role']
            session['user_team'] = user_dados['id_team']
            session.permanent = True

            print(f"Login bem-sucedido para o usuário: {user_dados['user_id']}")
            return jsonify({
                "mensagem": "Login bem-sucedido",
                "user": {
                    "name": user_dados['first_name'],
                    "email": email,
                    "role": user_dados['role'],
                }
            }), 200
        
    print(f"Falha no login para o email: {email}")
    return jsonify({"mensagem": "Email e/ou senha incorretos."}), 401


# Rota para verificar o status de login
@auth_bp.route('/status', methods=['GET'])
def status():
    user_id = session.get('user_id')
    
    if user_id:
        return jsonify({
            "isAuthenticated": True,
            "user": {
                "name": session.get('user_name'),
                "email": session.get('user_email'),
                "role": session.get('user_role')
            }
        }), 200
    return jsonify({"isAuthenticated": False}), 401

# Rota de logout
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_last_name', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.pop('user_team', None)
    return jsonify({"mensagem": "Logout bem-sucedido"}), 200