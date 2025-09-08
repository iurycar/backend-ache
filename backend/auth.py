# API imports
from flask import Blueprint, request, jsonify, session
from .db import conn
from pathlib import Path
import os

"""
    Esse arquivo é responsável por criar as rotas e os meios de autenticação
"""

def consulta_db(email):
    resultado = conn("SELECT", "AUTH", 'email', email,
    user_id=None,
    password_hash=None,
    name=None,
    last_name=None,
    role=None)

    return resultado

# Criação do Blueprint/Projeto da aplicação de autenticação
auth_bp = Blueprint('auth_bp', __name__)

# Rota de login
@auth_bp.route("/login", methods=['POST'])
def login():
    dados = request.json
    email = dados.get('email')
    password = dados.get('password')

    users_db = consulta_db(email)

    user_dados = users_db.get(email)

    if user_dados and user_dados['password_hash'] == password:
        session['user_id'] = user_dados['user_id']
        session['user_email'] = email
        session['user_name'] = user_dados['name']
        session['user_last_name'] = user_dados['last_name']
        session['user_role'] = user_dados['role']
        print(f"Login bem-sucedido para o usuário: {user_dados['user_id']}")

        return jsonify({
            "mensagem": "Login bem-sucedido",
            "user": {
                "id": user_dados['user_id'],
                "name": user_dados['name'],
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
    print(user_id)
    if user_id:
        return jsonify({
            "isAuthenticated": True,
            "user": {
                "id": user_id,
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
    session.pop('user_email', None)
    session.pop('user_role', None)
    return jsonify({"mensagem": "Logout bem-sucedido"}), 200
