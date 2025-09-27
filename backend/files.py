from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
from .from_to_mysql import to_mysql_inserir, from_mysql_extrair
from werkzeug.utils import secure_filename
from .db import consultaSQL
from pathlib import Path
import datetime
import uuid
import json
import re
import os

"""
    Esse arquivo é responsável por lidar com as requisições para upload, download e delete de arquivos armazenados. 
    Cria identificadores únicos para os dados recebidos e víncula ao usuário.
"""

diretorio = Path(__file__).parent

def load_metadata(id_team: str) -> "Dados do projeto":
    resultados = consultaSQL('SELECT', 'PROJECT', 
        'id_team', id_team,         # SELECIONA ONDE (WHERE) ID_TEAM = ID_TEAM
        id_file=None,               # OS ARGS KEY SÃO AS COLUNAS QUE EU QUERO QUE RETORNE
        original_name=None,
        import_date=None,
        project_name=None,
        id_team=None,
    )
    return resultados

def save_metadata(id_file: str, filename: str, timestamp: str, id_team: str, project_name: str) -> None:
    consultaSQL('INSERT', 'PROJECT', 
        id_file=id_file, 
        original_name=filename, 
        import_date=timestamp,
        project_name=project_name, 
        id_team=id_team,
    )

# Criação do Blueprint/Projeto da aplicação de upload/download de arquivos
file_bp = Blueprint('file_bp', __name__)



# Rota de upload de arquivos
@file_bp.route('/upload', methods=['POST'])
def upload():
    try:
        # O ID servirá para garantir que não haja conflito entre as requisições dos usuários
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
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

        # Pega a data e horário
        date = datetime.datetime.now().astimezone().isoformat()

        # Exemplo nome do projeto 'Projeto 1' em "Desafio Número 1_Projeto 1 - Exportado.xlsx"
        project_name_pattern = r'Projeto\s+([^-_]+)'  # Padrão regex para capturar o nome do projeto
        match = re.search(project_name_pattern, arquivo.filename) # Procura o padrão no nome do arquivo
        project_name = match.group(1).strip() if match else "Projeto Sem Nome"

        # Armazena os metadados do arquivo
        save_metadata(id_file, original_name, date, id_team, project_name)

        # Verifica se o id_file foi salvo corretamente no banco de dados
        project_metadata = consultaSQL('SELECT', 'PROJECT', 'id_file', id_file, id_file=None)
        if not project_metadata:
            print(f"Erro: Metadados do arquivo {id_file} não foram salvos no banco de dados.")
            return jsonify({'mensagem': 'Erro ao salvar os metadados do arquivo.'}), 500

        # Manda os dados da tabela para o MySQL
        to_mysql_inserir(id_file)

        # Atualiza start_date e end_date em lote (normalizando conclusion 0–1 ou 0–100)
        try:
            with ENGINE.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE sheet SET 
                        start_date = CASE WHEN (start_date IS NULL OR start_date = '')
                                AND (
                                    CASE WHEN COALESCE(conclusion,0) > 1 THEN COALESCE(conclusion,0)/100 
                                        ELSE COALESCE(conclusion,0) END ) > 0 THEN NOW()
                            ELSE start_date END,
                        end_date = CASE
                            WHEN (end_date IS NULL OR end_date = '')
                                AND (
                                    CASE WHEN COALESCE(conclusion,0) > 1 THEN COALESCE(conclusion,0)/100 
                                        ELSE COALESCE(conclusion,0) END ) >= 1 THEN NOW()
                            ELSE end_date END 
                        WHERE id_file = :id_file"""), {"id_file": id_file}
                )
        except Exception as error:
            print(f"Falha ao atualizar start/end_date em lote: {error}")
        print(f"Arquivo {original_name} salvo com ID único {id_file} para o usuário {user_id}")

        return jsonify({
            'mensagem': f'Arquivo {original_name} enviado e salvo com sucesso!',
            'arquivo_importado': id_file,
        }), 200

    except Exception as error:
        print(f"Erro ao fazer upload do arquivo: {error}")
        return jsonify({'mensagem': f"Ocorreu um erro: {error}"}), 500



# Rota de download de arquivos
@file_bp.route('/download/<id_file>', methods=['GET'])
def download(id_file: str):
    try:
        # Pega o user_id da sessão
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
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
        return jsonify({'mensagem': f"Ocorreu um erro: {error}"}), 501



# Rota para deletar algum arquivo solicitado
@file_bp.route('/delete/<id_file>', methods=['DELETE'])
def delete(id_file: str):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
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
            
            consultaSQL('DELETE', 'SHEET', 'id_file', id_file) # Deleta todas as linhas com a mesma FK
            consultaSQL('DELETE', 'PROJECT', 'id_file', id_file)  # Deleta os metadados do arquivo

            print(f"Arquivo {id_file} excluído com sucesso.")

            return jsonify({"mensagem": "Arquivo excluído com sucesso."}), 200
        else:
            return jsonify({"mensagem": "Arquivo não encontrado no servidor."}), 404

    except Exception as error:
        print(f"Erro ao deletar o arquivo: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"})



# Rota para solicitar os arquivos do usuário
@file_bp.route('/arquivos_usuario', methods=['GET'])
def arquivos_usuario():
    arquivos: list[dict] = []

    user_id = session.get('user_id')
    id_team = session.get('user_team')

    print(f"Recebendo requisição para 'arquivos_usuario'. User ID na sessão: {user_id}")

    if not user_id:
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
                'importedAt': meta['import_date']
            })
    #print(f"Lista de arquivos encontrada para o usuário {user_id}: {arquivos}")

    return jsonify({'arquivos': arquivos})



@file_bp.route('/arquivo/<id_file>/dados', methods=['GET'])
def enviar_dados(id_file):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        dados = consultaSQL('SELECT', 'SHEET', 'id_file', id_file,
            num=None,
            classe=None,
            category=None,
            phase=None,
            status=None,
            name=None,
            duration=None,
            text=None,
            reference=None,
            conclusion=None,
            start_date=None,
            end_date=None
        )

        # Converte datetime.datetime para ISO
        # Calcula o atraso (em dias) para cada tarefa
        # Não achei maneira mais eficiente de fazer isso :/
        for linha in dados:
            if isinstance(linha.get('start_date'), datetime.datetime):
                
                dt_inicio = linha['start_date']
                dias = linha.get('duration', 0)

                if dias.isdigit():
                    dias = int(dias)
                else:
                    dias = 0

                dt_fim = dt_inicio + datetime.timedelta(days=dias)
                dt_hoje = datetime.datetime.now(dt_inicio.tzinfo)

                print(f"Calculando atraso para linha {linha.get('num')}:")
                print(f"  Data de início: {dt_inicio}")
                print(f"  Data atual: {dt_hoje}")
                print(f"  Duração (dias): {dias}")
                print(f"  Data de fim calculada: {dt_fim}")

                if dt_fim < dt_hoje:
                    atraso = (dt_hoje - dt_fim).days
                else:
                    atraso = 0

                print(f"Atraso calculado para linha {linha.get('num')}: {atraso} dias")
                
                linha['atraso'] = atraso
                linha['start_date'] = linha['start_date'].isoformat()
        #Start date: 2025-09-26
        if not dados:
            return jsonify({"mensagem": "Informações da planilha não encontrada."}), 404

        return jsonify({'dados': dados}), 200

    except Exception as error:
        print(f"Erro ao buscar todas as tarefas: {error}")


# Rota para atualizar uma linha da planilha
@file_bp.route('/arquivo/<id_file>/linha/<int:num>', methods=['PATCH'])
def atualizar_linha(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        data = request.get_json(silent=True) or {} # Dados enviados na requisição

        # Campos permitidos para atualização
        permitidos = {
            'num', 'classe', 'category', 'phase', 'status',
            'name', 'duration', 'text', 'reference', 'conclusion'
        }

        # Filtra apenas os campos permitidos
        update_args: dict = {}
        for key, value in data.items():
            if key not in permitidos:
                return jsonify({"mensagem": f"Campo inválido para atualização: {key}"}), 400
            else:
                update_args[key] = value

        print("Update: ", data)
        print("Update args: ", update_args)

        # Normaliza conclusion (0-1)
        if 'conclusion' in update_args:
            try:
                c = float(update_args['conclusion'])
                # aceita 0–100 e 0–1; se c>1, converte para 0–1
                if c <= 1:
                    update_args['conclusion'] = c
                else:
                    update_args['conclusion'] = min(max(c / 100, 0), 1)
            except Exception:
                update_args.pop('conclusion', None)

        if not update_args:
            return jsonify({"mensagem": "Nada para atualizar."}), 400

        print(f"Atualizando linha {num} do arquivo {id_file} com: {update_args}")
        
        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None
        )

        if not linha_existente:
            num = str(consultaSQL("SELECT", "SHEET", "id_file", id_file[0], "MAX(num)") + 1)

            consultaSQL('INSERT', 'SHEET',
                id_file = id_file,
                num = num,
                classe = update_args.get('classe', ''),
                category = update_args.get('category', ''),
                phase = update_args.get('phase', ''),
                status = update_args.get('status', '').strip().upper(),
                name = update_args.get('name', ''),
                duration = update_args.get('duration', ''),
                text = update_args.get('text', ''),
                reference = update_args.get('reference', ''),
                conclusion = update_args.get('conclusion', 0)
            )

            return jsonify({
                "mensagem": "Linha inserida com sucesso.",
                "inserted": update_args
            }), 201
        else:
            # Executa o UPDATE na linha alvo (chave: id_file + num atual)
            # Observação: se 'num' estiver em update_args, ele será o NOVO valor.
            consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'num', num, **update_args)

        return jsonify({
            "mensagem": "Linha atualizada com sucesso.",
            "updated": update_args
        }), 200

    except Exception as error:
        print(f"Erro ao atualizar linha: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


# Rota para deletar uma linha da planilha
@file_bp.route('/arquivo/<id_file>/linha/<int:num>', methods=['DELETE'])
def deletar_linha(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        # Executa o DELETE na linha alvo (chave: id_file + num atual)
        consultaSQL('DELETE', 'SHEET', 'id_file', id_file, 'num', num)

        return jsonify({"mensagem": "Linha deletada com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao deletar linha: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


# Rota para iniciar uma tarefa
@file_bp.route('/arquivo/<id_file>/start/<int:num>', methods=['POST'])
def iniciar_tarefa(id_file: str, num: int):
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None,
            start_date=None
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        start = linha_existente[0]['start_date']
        if start:
            return jsonify({"mensagem": "A tarefa já está em andamento."}), 400

        date = datetime.datetime.now().astimezone().isoformat()

        # Atualiza o status da tarefa para "EM ANDAMENTO"
        consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'num', num, start_date=date)

        return jsonify({"mensagem": "Tarefa iniciada com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao iniciar tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500


# Rota para desfazer o início de uma tarefa
@file_bp.route('/arquivo/<id_file>/start/<int:num>', methods=['DELETE'])
def desfazer_inicio_tarefa(id_file: str, num: int):
    """Remove o start_date (volta tarefa para 'não iniciada' em termos de início)."""
    try:
        user_id = session.get('user_id')
        id_team = session.get('user_team')

        if not user_id or not id_team:
            return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401

        # Verifica se o arquivo pertence ao time do usuário
        metadado_arquivo_importado = load_metadata(id_team)
        if not metadado_arquivo_importado or id_file not in metadado_arquivo_importado:
            return jsonify({"mensagem": "Arquivo não encontrado."}), 404

        # Verifica se a linha existe
        linha_existente = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'num', num,
            id_file=None,
            num=None,
            conclusion=None,
            start_date=None
        )

        if not linha_existente:
            return jsonify({"mensagem": "Linha não encontrada."}), 404

        start = linha_existente[0].get('start_date')
        if not start:
            return jsonify({"mensagem": "A tarefa ainda não foi iniciada."}), 400

        if linha_existente[0].get('conclusion', 0) == 1:
            return jsonify({"mensagem": "A tarefa já foi concluída; não é possível desfazer o início."}), 400

        # Define start_date como NULL
        consultaSQL('UPDATE', 'SHEET', 'id_file', id_file, 'num', num, start_date=None, conclusion=0)

        return jsonify({"mensagem": "Início da tarefa removido com sucesso."}), 200

    except Exception as error:
        print(f"Erro ao desfazer início de tarefa: {error}")
        return jsonify({"mensagem": f"Ocorreu um erro: {error}"}), 500



@file_bp.route('/arquivo/<id_file>/add_task', methods=['POST'])
def adicionar_tarefa(id_file: str):
    dados = request.get_json(silent=True) or {}

    user_id = session.get('user_id')
    id_team = session.get('user_team')

    if not user_id or not id_team:
        return jsonify({"mensagem": "Acesso negado. Por favor, faça login."}), 401
    
