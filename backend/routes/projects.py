from flask import Blueprint, jsonify, session, request
import datetime

from backend.services.progress import get_progress, rows_list
from backend.services.db import consultaSQL

project_bp = Blueprint('project_bp', __name__)

@project_bp.route("/projects/data", methods=['GET'])
def get_projects_data():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        data: list[dict] = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file},
            colunas_dados={
                'duration': None,
                'conclusion': None,
                'start_date': None,
                'end_date': None,
                'user_id': None,
            }
        )

        return jsonify({'data': data}), 200

    except Exception as error:
        print(f"Erro ao buscar dados dos projetos: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


@project_bp.route("/projects/completed", methods=['POST'])
def set_project_completed():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        print(f"Recebendo requisição para 'project_completed'. User ID na sessão: {user_id}")

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        body = request.get_json(silent=True) or {}

        id_file = body.get('id_file')

        if not id_file:
            return jsonify({"mensagem": "ID do arquivo do projeto é obrigatório."}), 400

        consulta: dict = consultaSQL(
            'SELECT', 'PROJECTS', 
            where={'id_file': id_file}, 
            colunas_dados={'completed': None}
        )
        
        project_rows = rows_list(consulta)

        if not consulta:
            return jsonify({"mensagem": "Projeto não encontrado."}), 404

        if int(project_rows[0].get('completed', 0)) == 1:
            return jsonify({'mensagem': "O projeto já foi concluído."}), 200

        consulta: list[dict] = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file}, 
            colunas_dados={'conclusion': None, 'num': None}
        )

        for linha in consulta:
            if float(linha.get('conclusion', 0)) < 1:
                return jsonify({'mensagem': f"A tarefa {linha.get('num')} ainda não foi concluída."}), 200

        consultaSQL('UPDATE', 'PROJECTS', where={'id_file': id_file}, colunas_dados={'completed': 1})

        consulta: list[dict] = consultaSQL(
            'SELECT', 'TEAMS', 
            where={'id_team': id_team}, 
            campo={'MAX': 'completed_projects'}
        )

        max_completed: int = 0
        if isinstance(consulta, list) and consulta:
            row: dict = consulta[0]
            max_completed = int(row.get('MAX(completed_projects)', 0) or 0) # Se for None, usa 0        

        max_completed += 1

        consultaSQL(
            'UPDATE', 'TEAMS', 
            where={'id_team': id_team},
            colunas_dados={'completed_projects': max_completed}
        )

        date = datetime.datetime.now().astimezone().isoformat()

        consultaSQL(
            'UPDATE', 'PROJECTS',
            where={'id_file': id_file},
            colunas_dados={'closing_date': date}
        )

        print(f"Projeto {id_file} marcado como concluído.")

        return jsonify({'mensagem': "Projeto marcado como concluído com sucesso."}), 200
    except Exception as error:
        print(f"Erro ao buscar dados dos projetos: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para buscar o progresso das tarefas do projeto
@project_bp.route('/project/progress_tasks/<id_file>', methods=['GET'])
def get_tasks_project_progress(id_file: str):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Retornar progresso = {'total': X, 'concluidas': Y, 'em andamento': Z, 'não iniciadas': W, 'atrasadas': V}

        progresso: dict = get_progress(id_file, id_team)

        return jsonify({"progresso": progresso}), 200

    except Exception as error:
        print(f"Erro ao buscar progresso das tarefas do projeto: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


@project_bp.route('/project/completed', methods=['GET'])
def get_completed_projects():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        progresso, labels, tasks, projects = get_progress('', id_team, by_month=True)

        return jsonify({
            'labels': labels,
            'tasks_concluded': tasks,
            'project_concluded': projects,
            'raw': progresso
        }), 200

    except Exception as error:
        print(f"Erro ao buscar projetos concluídos: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500