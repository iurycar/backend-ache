from .db import consultaSQL
import datetime
import re

""" Esse arquivo é responsável por lidar com o progresso das tarefas, como calcular atrasos e obter o progresso geral. """

def calculate_delay(data: list[dict], total: bool = False) -> dict | int:
    """ Calcula o atraso das tarefas individualmente ou o total de tarefas atrasadas """

    for row in data:
        completed = row.get('conclusion', 0)

        if completed and completed >= 1:
            row['atraso'] = 0
            continue

        #print(f"Processando linha: {row}")

        start_date = row.get('start_date')

        if not start_date or start_date == '' or start_date is None:
            row['atraso'] = 0
            row['start_date'] = None
            continue

        deadline = row.get('deadline')
        duration = row.get('duration')

        #print(f"Data de início para linha {row.get('num')}: {start_date}")
        
        if isinstance(start_date, datetime.datetime):
            dt_inicio = start_date
        elif isinstance(start_date, str):
            try:
                dt_inicio = datetime.datetime.fromisoformat(start_date)
            except Exception:
                continue
        else:
            continue

        #print(f"Duração original para linha {row.get('num')}: {row.get('duration')} dias.")

        if isinstance(deadline, datetime.datetime):
            dt_deadline = deadline
        elif isinstance(deadline, str):
            try:
                dt_deadline = datetime.datetime.fromisoformat(deadline)
            except Exception:
                continue
        else:
            continue

        now = datetime.datetime.now(dt_inicio.tzinfo)

        if now > dt_deadline:
            atraso = (now - dt_deadline).days
        else:
            atraso = 0

        #print(f"Calculando atraso para linha {row.get('num')}:")
        #print(f"  Data atual: {now}")
        #print(f"  Data de início: {start_date}")
        #print(f"  Duração (dias): {duration}")
        #print(f"  Data de fim calculada: {dt_deadline}")
        #print(f"  Atraso encontrado: {atraso if atraso > 0 else 0} dias")

        #print(f"Atraso calculado para linha {row.get('num')}: {atraso} dias\n")
        
        row['atraso'] = atraso
        row['start_date'] = row['start_date'].isoformat()

    return data


def get_progress(id_file: str, id_team: str, user_id: str = None, by_month: bool = False) -> dict | tuple[dict[str, int], list[str], list[int]]:
    """ Obtém o progresso das tarefas de um projeto ou do time, podendo ser agrupado por mês 
        @param id_file: ID do arquivo/projeto
        @param id_team: ID do time
        @param user_id: ID do usuário (opcional)
        @param by_month: Se True, agrupa o progresso por mês
    """
    
    if by_month:
        progresso = {}
    
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month
        
        pt_month = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

        labels: list[str] = []
        tasks: list[int] = []
        projects: list[int] = []

        if not id_file or (isinstance(id_file, str) and id_file.strip().lower() in ('null', 'all')):
            id_file = ''

        # Conta por mês
        for i in range(1, current_month + 1):
            
            tarefas_rows: list[dict] = consultaSQL(
                'SELECT', 'SHEETS',
                where={
                    'conclusion': 1,
                    'id_team': id_team,
                },
                where_especial={
                    'SQL:MONTH(`end_date`)': f'= {i}',
                    'SQL:YEAR(`end_date`)': f'= {current_year}'
                },
                campo={'JOIN ON': ['PROJECTS', 'id_file']},
                colunas_dados={
                    'SQL:COUNT(*)': None
                }
            )
            tarefas_count = int((tarefas_rows and tarefas_rows[0].get('COUNT(*)', 0) or 0))

            projetos_rows: list[dict] = consultaSQL(
                'SELECT', 'PROJECTS',
                where={
                    'id_team': id_team,
                    'completed': 1,
                },
                where_especial={
                    'SQL:MONTH(`closing_date`)': f'= {i}', 
                    'SQL:YEAR(`closing_date`)': f'= {current_year}'
                },
                colunas_dados={
                    'SQL:COUNT(*)': None
                }
            )

            projetos_count = int((projetos_rows and projetos_rows[0].get('COUNT(*)', 0) or 0))

            month = pt_month[i - 1]

            progresso[month] = {
                'project_concluded': projetos_count,
                'tasks_concluded': tarefas_count,
            }

            labels.append(month)
            tasks.append(tarefas_count)
            projects.append(projetos_count)

        return progresso, labels, tasks, projects
    else:
        # Se caso qualquer coluna tiver valor '', a coluna não será considerada na consulta
        if id_file is None or id_file.lower() == 'null' or id_file.strip() == 'all':
            id_file = ''
        
        if user_id is None or user_id.lower() == 'null':
            user_id = ''

        progresso = {
            'total': 0,
            'concluded': 0,
            'not_started': 0,
            'in_progress': 0,
            'overdue': 0
        }

        # SELECT COUNT(*) FROM SHEETS JOIN PROJECTS ON SHEETS.id_file = PROJECTS.id_file WHERE id_team = ? AND SHEETS.id_file = ? AND user_id = ?
        consulta = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_team': id_team, 'SHEETS`.`id_file': id_file, 'user_id': user_id,},
            campo={'JOIN ON': ['PROJECTS', 'id_file']},
            colunas_dados={
                'SQL:COUNT(*)': None
            }
        )
        
        total = int(consulta[0].get('COUNT(*)', 0) or 0)

        consulta = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_team': id_team, 'SHEETS`.`id_file': id_file, 'user_id': user_id, 'conclusion': 1},
            campo={'JOIN ON': ['PROJECTS', 'id_file']},
            colunas_dados={
                'SQL:COUNT(*)': None
            }
        )

        concluidas = int(consulta[0].get('COUNT(*)', 0) or 0)

        consulta = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_team': id_team, 'SHEETS`.`id_file': id_file, 'user_id': user_id, 'conclusion': 0},
            where_especial={'start_date': 'IS NULL', 'end_date': 'IS NULL'},
            campo={'JOIN ON': ['PROJECTS', 'id_file']},
            colunas_dados={
                'SQL:COUNT(*)': None
            }
        )

        nao_iniciadas = int(consulta[0].get('COUNT(*)', 0) or 0)

        consulta = consultaSQL(
            'SELECT', 'SHEETS', 
            where={'id_team': id_team, 'SHEETS`.`id_file': id_file, 'user_id': user_id,},
            where_especial={'conclusion': ['> 0', '< 1']},
            campo={'JOIN ON': ['PROJECTS', 'id_file']},
            colunas_dados={
                'id_task': None,
                'num': None,
                'start_date': None,
                'deadline': None,
                'duration': None,
                'conclusion': None
            }
        )

        em_andamento = consulta

        progresso['total'] += total
        progresso['concluded'] += concluidas
        progresso['not_started'] += nao_iniciadas

        em_rows = rows_list(em_andamento)

        in_progress = len(em_rows)

        #print(f"Tarefas em andamento para o arquivo {id_file}: {in_progress}")

        # select count(*) as `overdue` from `SHEETS` where `start_date` is not null and `deadline` is not null and datediff(NOW(), `deadline`) > 0;
        overdue_tasks = consultaSQL(
            'SELECT', 'SHEETS',
            where={'id_team': id_team, 'SHEETS`.`id_file': id_file, 'user_id': user_id},
            where_especial={'deadline': 'IS NOT NULL', 'start_date': 'IS NOT NULL', 'SQL:datediff(NOW(), `deadline`)': '> 0'},
            campo={'JOIN ON': ['PROJECTS', 'id_file']},
            colunas_dados={
                'SQL:COUNT(*)': None
            }
        )

        overdue_count = int(overdue_tasks[0].get('COUNT(*)', 0) or 0)

        in_progress_count = max(in_progress - overdue_count, 0)

        progresso['in_progress'] += in_progress_count
        progresso['overdue'] += overdue_count

        return progresso


def rows_list(result) -> list[dict]:
    if isinstance(result, dict):
        return list(result.values())
    if isinstance(result, list):
        return result
    return []