from flask import Blueprint, jsonify, session, request
import datetime

from backend.services.db import consultaSQL
from .files import load_metadata

""" Esse arquivo é responsável por lidar com o gerenciamento de tarefas, como iniciar e parar tarefas. """

tasks_bp = Blueprint('tasks_bp', __name__)

# Rota para iniciar uma tarefa
@tasks_bp.route('/arquivo/<id_file>/start/<int:num>', methods=['POST'])
def set_started_task(id_file: str, num: int):
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
        linha_existente = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file, 'num': num},
            colunas_dados={'id_file': None, 'num': None, 'start_date': None, 'duration': None}
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        start = linha_existente[0]['start_date']
        if start:
            return jsonify({"mensagem": "A tarefa já está em andamento."}), 400

        date = datetime.datetime.now()

        # Atualiza o status da tarefa para "EM ANDAMENTO"
        consultaSQL(
            'UPDATE', 'SHEETS', 
            where={'id_file': id_file, 'num': num},
            colunas_dados={'start_date': date, 'user_id': user_id}
        )

        # Calcula e define o deadline (prazo) com base na duração
        consultaSQL(
            'UPDATE', 'SHEETS',
            where={'id_file': id_file, 'num': num},
            colunas_dados={'deadline': 'SQL:DATE_ADD(`start_date`, INTERVAL `duration` DAY)'}
        )

        return jsonify({"mensagem": "Tarefa iniciada com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao iniciar tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para desfazer o início de uma tarefa
@tasks_bp.route('/arquivo/<id_file>/start/<int:num>', methods=['DELETE'])
def set_not_started_task(id_file: str, num: int):
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
        linha_existente = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file, 'num': num},
            colunas_dados={
                'id_file': None,
                'num': None,
                'conclusion': None,
                'start_date': None
            }
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        start = linha_existente[0].get('start_date')
        if not start:
            return jsonify({"mensagem": "A tarefa ainda não foi iniciada."}), 400

        if linha_existente[0].get('conclusion', 0) == 1:
            return jsonify({"mensagem": "A tarefa já foi concluída; não é possível desfazer o início."}), 400

        # Define start_date como NULL
        consultaSQL(
            'UPDATE', 'SHEETS', 
            where={'id_file': id_file, 'num': num},
            colunas_dados={
                'start_date': None, 
                'conclusion': 0
            }
        )

        return jsonify({"mensagem": "Início da tarefa removido com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao desfazer início de tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para atualizar/adicionar uma linha da planilha
@tasks_bp.route('/arquivo/<id_file>/linha/<int:num>', methods=['PATCH'])
def update_add_task(id_file: str, num: int):
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

        print(f"\nDados recebidos para atualizar/Adicionar linha {num} do arquivo {id_file}: {data}\n")

        if 'responsible' in data:
            data['user_id'] = data.pop('responsible')

        if data.get('user_id') in ('', 'null'):
            data['user_id'] = None

        # Campos permitidos para atualização
        permitidos = {
            'num', 'classe', 'category', 'phase', 'status',
            'name', 'duration', 'text', 'reference', 'conclusion',
            'user_id'
        }

        # Filtra apenas os campos permitidos
        update_args: dict = {}
        for key, value in data.items():
            if key not in permitidos:
                print(f"\nCampo inválido para atualização: {key}")
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

        print("\nUpdate: ", data)
        print("\nUpdate args: ", update_args)

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
        linha_existente = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file, 'num': num},
            colunas_dados={'id_file': None, 'num': None}
        )

        print(f"\nLinha existente: {linha_existente}")

        # Se a linha não existir, insere uma nova linha
        if not linha_existente:
            # calcular próximo número de linha para este arquivo
            try:
                max_result = consultaSQL(
                    'SELECT', 'SHEETS', 
                    where={'id_file': id_file}, 
                    colunas_dados={},
                    campo={'MAX': 'num'}
                )

                print("\nMax result:", max_result)

                max_num: int = 0
                if isinstance(max_result, list) and max_result:
                    # chave pode ser 'MAX(num)' dependendo do SELECT
                    row = max_result[0]
                    max_num = int(row.get('MAX(num)', 0) or 0) # Se for None, usa 0
            except Exception:
                max_num = 0

            novo_num: int = max_num + 1

            print(f"\nInserindo nova linha {novo_num} no arquivo {id_file} com: {update_args}\n")

            consultaSQL(
                'INSERT', 'SHEETS',
                colunas_dados= {
                    'id_file': id_file,
                    'num': novo_num,
                    'classe': update_args.get('classe', ''),
                    'category': update_args.get('category', ''),
                    'phase': update_args.get('phase', ''),
                    'status': (update_args.get('status', '') or '').strip().lower().capitalize(),
                    'name': update_args.get('name', ''),
                    'duration': update_args.get('duration', '').replace(' dias', ''),
                    'text': "Texto."+str(novo_num),
                    'reference': "Doc."+str(novo_num),
                    'conclusion': update_args.get('conclusion', 0),
                    'user_id': update_args.get('user_id', '')
                }
            )

            return jsonify({
                "mensagem": "Linha inserida com sucesso.",
                "inserted": {**update_args, 'num': novo_num}
            }), 201
        else:
            print(f"Atualizando linha {num} do arquivo {id_file} com: {update_args}")

            if 'duration' in update_args:
                update_args['duration'] = update_args['duration'].replace(' dias', '')

            # Executa o UPDATE na linha alvo (chave: id_file + num atual)
            consultaSQL(
                'UPDATE', 'SHEETS', 
                where={'id_file': id_file, 'num': num},
                colunas_dados=update_args
            )

            return jsonify({
                "mensagem": "Linha atualizada com sucesso.",
                "updated": update_args
            }), 200

    except Exception as error:
        print(f"Erro ao atualizar linha: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500


# Rota para deletar uma linha da planilha
@tasks_bp.route('/arquivo/<id_file>/linha/<int:num>', methods=['DELETE'])
def delete_task(id_file: str, num: int):
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
        linha_existente = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_file': id_file, 'num': num},
            colunas_dados={'id_file': None, 'num': None}
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        # Executa o DELETE na linha alvo (chave: id_file + num atual)
        consultaSQL(
            'DELETE', 'SHEETS', 
            where={'id_file': id_file, 'num': num}
        )

        return jsonify({"mensagem": "Linha deletada com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao deletar linha: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro."}), 500
