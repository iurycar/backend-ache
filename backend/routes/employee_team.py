from flask import Blueprint, jsonify, request, session
import datetime

from backend.services.db import consultaSQL
from backend.services.progress import *

employee_team_bp = Blueprint('employee_team_bp', __name__)

# Rota para buscar os funcionários do time
@employee_team_bp.route('/team/employees', methods=['GET'])
def get_team_employees():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Buscar todos os funcionários do time
        employees: list[dict] = consultaSQL(
            'SELECT', 'EMPLOYEES', 
            where={'id_team': id_team}, 
            colunas_dados={
                'first_name': None, 
                'last_name': None, 
                'user_id': None
            }
        )

        valid_response: list[dict] = []

        # Filtra apenas os funcionários com nome e sobrenome válidos
        for emp in employees:
            name_and_id: dict = {}
            first_name: str = emp.get('first_name', '').strip()
            last_name: str = emp.get('last_name', '').strip()
            id_employee: str = emp.get('user_id', '').strip()

            if first_name and last_name:
                name_and_id['name'] = f"{first_name} {last_name}"
            elif first_name:
                name_and_id['name'] = first_name

            if name_and_id:
                name_and_id['id'] = id_employee
                valid_response.append(name_and_id)

        print(f"Funcionários encontrados para o time {id_team}: {valid_response}")

        return jsonify({'employees': valid_response}), 200
    except Exception as error:
        print(f"Erro ao buscar funcionários do time: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


@employee_team_bp.route('/team/info', methods=['POST'])
def get_info_team():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        consulta: list[dict] = consultaSQL(
            'SELECT', 'EMPLOYEES', 
            where={'id_team': id_team}, 
            colunas_dados={
                'user_id': None,
                'email': None,
                'first_name': None,
                'last_name': None,
                'role': None,
                'cellphone': None,
                'active': None,
                'id_address': None
            }
        )

        if not consulta:
            return jsonify({"mensagem": "Nenhum funcionário encontrado para este time."}), 404
        
        for emp in consulta:
            address: list[dict] = consultaSQL(
                'SELECT', 'ADDRESS',
                where={'id_address': emp.get('id_address')},
                colunas_dados={
                    'street_address': None,
                    'city': None,
                    'state': None,
                    'country': None
                }
            )

            if address:
                emp['address'] = {'street': address.get('street_address', ''),'city': address.get('city', ''), 'state': address.get('state', ''), 'country': address.get('country', '')}
            else:
                emp['address'] = {'city': None, 'state': None, 'country': None}

            # Contagem de tarefas concluídas por funcionário
            consulta_tasks: list[dict] = consultaSQL(
                'SELECT', 'SHEETS',
                where={'user_id': emp.get('user_id'), 'conclusion': 1},
                colunas_dados={},
                campo={'COUNT': '*'}
            )

            count_tasks = 0
            
            if isinstance(consulta_tasks, list) and consulta_tasks:
                row = consulta_tasks[0]
                count_tasks = int(row.get('COUNT(*)', 0) or 0)
            emp['completed_tasks'] = count_tasks

        # Projetos em andamento no time
        projects: list[dict] = consultaSQL(
            'SELECT', 'PROJECTS',
            where={'id_team': id_team, 'completed': 0},
            colunas_dados={},
            campo={'COUNT': '*'}
        )

        if isinstance(projects, list) and projects:
            consulta[0]['ongoing_projects'] = int(projects[0].get('COUNT(*)', 0) or 0)
        else:
            consulta[0]['ongoing_projects'] = 0

        # Nome da equipe
        team_name: list[dict] = consultaSQL(
            'SELECT', 'TEAMS',
            where={'id_team': id_team},
            colunas_dados={'name_team': None}
        )

        if isinstance(team_name, list) and team_name:
            consulta[0]['team_name'] = team_name[0].get('name_team', '')

        #print(f"Informações do time {id_team}: {consulta}")

        return jsonify({'employees': consulta}), 200
    except Exception as error:
        print(f"Erro ao buscar funcionários do time: {error}")
        return jsonify({"mensagem": "Ocorreu um erro."}), 500


@employee_team_bp.route('/team/progress', methods=['GET'])
def get_team_progress():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        completed_projects: list[dict] = consultaSQL(
            'SELECT', 'PROJECTS',
            where={'id_team': id_team, 'completed': 1},
            campo={'COUNT': '*'}
        )

    except Exception as error:
        print(f"Erro ao buscar progresso do time: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para buscar as tarefas atribuídas a um funcionário específico
@employee_team_bp.route('/employee/tasks/<id_employee>/<id_file>', methods=['GET'])
def get_employee_tasks_detail(id_employee: str, id_file: str):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
        
        if not id_employee or id_employee.strip() in ('', 'null', 'undefined'):
            return jsonify({"mensagem": "ID do funcionário inválido."}), 400

        if not id_file or id_file.strip() in ('', 'undefined'):
            return jsonify({"mensagem": "ID do arquivo inválido."}), 400

        print(f"Buscando tarefas para o funcionário '{id_employee}' no projeto '{id_file}' do time '{id_team}'")

        if id_file != 'null':
            # Buscar todas as tarefas atribuídas ao funcionário no projeto especificado
            tarefas: list[dict] = consultaSQL(
                'SELECT', 'SHEETS', 
                where={'user_id': id_employee, 'id_file': id_file},
                colunas_dados={
                    'num': None,
                    'name': None,
                    'SQL:CONCAT(`duration`, " dias") AS `duration`': None,
                    'conclusion': None,
                    'start_date': None,
                    'deadline': None,
                    'end_date': None
                }
            )
        else:
            # Buscar todas as tarefas atribuídas ao funcionário em todos os projetos do time
            tarefas: list[dict] = consultaSQL(
                'SELECT', 'SHEETS',
                where={'user_id': id_employee},
                colunas_dados={
                    'num': None,
                    'name': None,
                    'SQL:CONCAT(`duration`, " dias") AS `duration`': None,
                    'conclusion': None,
                    'start_date': None,
                    'deadline': None,
                    'end_date': None
                }
            )

        if not tarefas:
            return jsonify({"mensagem": "Nenhuma tarefa encontrada para este funcionário no projeto."}), 404

        if id_file != 'null':
            completed = consultaSQL(
                'SELECT', 'PROJECTS', 
                where={'id_file': id_file, 'user_id': id_employee}, 
                colunas_dados={'completed': None}
            )

            if completed and completed[0].get('completed', 0) == 0:
                tarefas = calculate_delay(tarefas)
        else:
            tarefas = calculate_delay(tarefas)

        # Organizar as tarefas por status
        progresso: dict = get_progress(id_file, id_team, user_id=id_employee)
        #print(f"Tarefas encontradas para o funcionário '{id_employee}': {tarefas}")
        #print(f"Progresso das tarefas para o funcionário '{id_employee}': {progresso}")

        return jsonify({
            "tasks": tarefas,
            "progress": progresso
        }), 200

    except Exception as error:
        print(f"Erro ao buscar tarefas do funcionário: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


@employee_team_bp.route('/employee/tasks/gantt', methods=['GET'])
def get_employee_tasks():
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Buscar todas as tarefas atribuídas ao funcionário na equipe
        tarefas: list[dict] = consultaSQL(
            'SELECT', 'SHEETS',
            where={'user_id': user_id},
            campo={'JOIN ON': ['PROJECTS', 'id_file']},
            colunas_dados={
                'num': None,
                'name': None,
                'status': None,
                'duration': None,
                'conclusion': None,
                'start_date': None,
                'deadline': None,
                'end_date': None,
                'project_name': None,
                'SQL:SHEETS.id_file AS id_file': None
            }
        )

        if not tarefas:
            return jsonify({"mensagem": "Nenhuma tarefa encontrada para este funcionário."}), 404

        #print(f"Tarefas encontradas para o funcionário '{user_id}': {tarefas}")
        #tarefas = calculate_delay(tarefas)

        return jsonify({
            "tasks": tarefas
        }), 200

    except Exception as error:
        print(f"Erro ao buscar tarefas do funcionário: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


@employee_team_bp.route('/employee/tasks/gantt/update/<id_file>/<int:num>', methods=['PATCH'])
def update_employee_task(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if (not user_id or not id_team) or (user_id is None or id_team is None):
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        data = request.get_json(silent=True) or {} # Dados enviados na requisição

        print(f"\nDados recebidos para atualizar tarefa {num} do arquivo {id_file}: {data}\n")

        # Campos permitidos para atualização
        permitidos = {
            'duration',
            'conclusion'
        }

        # Filtra apenas os campos permitidos
        update_args: dict = {}
        for key, value in data.items():
            if key not in permitidos:
                print(f"\nCampo inválido para atualização: {key}")
                return jsonify({"mensagem": f"Campo inválido para atualização: {key}"}), 400
            else:
                update_args[key] = value

        if not update_args:
            return jsonify({"mensagem": "Nada para atualizar."}), 400

        linha_existente: list[dict] = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file, 'num': num, 'user_id': user_id},
            colunas_dados={'id_file': None, 'num': None}
        )

        if not linha_existente:
            try:
                max_result: list[dict] = consultaSQL(
                    'SELECT', 'SHEETS', 
                    where={'id_file': id_file}, 
                    colunas_dados={},
                    campo={'MAX': 'num'}
                )

                max_num: int = 0
                if isinstance(max_result, list) and max_result:
                    # chave pode ser 'MAX(num)' dependendo do SELECT
                    row = max_result[0]
                    max_num = int(row.get('MAX(num)', 0) or 0) # Se for None, usa 0
            except Exception:
                max_num = 0
            
            novo_num: int = max_num + 1

            consultaSQL(
                'INSERT', 'SHEETS',
                colunas_dados= {
                    'id_file': id_file,
                    'num': novo_num,
                    'duration': update_args.get('duration', '').replace(' dias', ''),
                    'conclusion': update_args.get('conclusion', 0),
                    'user_id': update_args.get('user_id', '')
                }
            )

            return jsonify({
                "mensagem": "Linha inserida com sucesso.",
                "inserted": {**update_args, 'num': novo_num}
            }), 201
        else:
            # Executa o UPDATE na linha alvo (chave: id_file + num atual)
            consultaSQL(
                'UPDATE', 'SHEETS', 
                where={'id_file': id_file, 'num': num, 'user_id': user_id},
                colunas_dados=update_args
            )

            return jsonify({
                "mensagem": "Tarefa atualizada com sucesso.",
                "updated": update_args
            }), 200

    except Exception as error:
        print(f"Erro ao atualizar tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500