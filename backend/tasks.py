from .db import consultaSQL
import datetime
import re

def duration_to_days(duration) -> int:
    """Converte uma duração em dias para valor numérico. Remove 'dias' da string."""
    
    # Retorna 0 se duration for None ou vazio
    if not duration or duration is None:
        return 0
    
    # Se for um número, assume que já está em dias
    if isinstance(duration, (int, float)):
        try:
            return int(float(duration))
        except Exception:
            return 0
    
    texto = str(duration).strip()

    # Usa regex para encontrar o primeiro número na string
    match = re.search(r'(\d+(?:[.,]\d+)?)', texto)

    if not match:
        return 0

    try:
        return int(float(match.group(1).replace(',', '.')))
    except Exception:
        return 0


def calculate_delay(data: list[dict]) -> dict:
    # Calcula o atraso (em dias) para cada tarefa
    # Não achei maneira mais eficiente de fazer isso :/
    for row in data:
        completed = row.get('conclusion', 0)

        if completed and completed >= 1:
            row['atraso'] = 0
            continue

        #print(f"Processando linha: {row}")

        dt_valor = row.get('start_date')

        if not dt_valor or dt_valor == '' or dt_valor is None:
            row['atraso'] = 0
            row['start_date'] = None
            continue

        print(f"Duração original para linha {row.get('num')}: {row.get('duration')}")

        if isinstance(dt_valor, datetime.datetime):
            dt_inicio = dt_valor
        elif isinstance(dt_valor, str) and dt_valor.strip():
            try:
                dt_inicio = datetime.datetime.fromisoformat(dt_valor)
            except Exception:
                continue
        else:
            continue

        dias: int = duration_to_days(row.get('duration'))
        prazo = (dt_inicio + datetime.timedelta(days=dias)).date()
        dt_hoje = datetime.datetime.now(dt_inicio.tzinfo).date()

        atraso = max((dt_hoje - prazo).days, 0)

        dt_fim = dt_inicio + datetime.timedelta(days=dias)
        dt_hoje = datetime.datetime.now(dt_inicio.tzinfo)

        print(f"Calculando atraso para linha {row.get('num')}:")
        print(f"  Data de início: {dt_inicio}")
        print(f"  Data atual: {dt_hoje}")
        print(f"  Duração (dias): {dias}")
        print(f"  Data de fim calculada: {prazo}")

        print(f"Atraso calculado para linha {row.get('num')}: {atraso} dias\n")
        
        row['atraso'] = atraso
        row['start_date'] = row['start_date'].isoformat()

    return data


def get_progress(id_file: str, id_team: str, user_id: str = None) -> dict:
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

    consulta = consultaSQL(
        'SELECT', 'SHEET', 
        where={'id_team': id_team, 'SHEET`.`id_file': id_file, 'user_id': user_id,},
        campo={'JOIN ON': ['PROJECT', 'id_file']},
        colunas_dados={
            'COUNT(*)': None
        }
    )
    
    total = int(consulta[0].get('COUNT(*)', 0) or 0)

    consulta = consultaSQL(
        'SELECT', 'SHEET', 
        where={'id_team': id_team, 'SHEET`.`id_file': id_file, 'user_id': user_id, 'conclusion': 1},
        campo={'JOIN ON': ['PROJECT', 'id_file']},
        colunas_dados={
            'COUNT(*)': None
        }
    )

    concluidas = int(consulta[0].get('COUNT(*)', 0) or 0)

    consulta = consultaSQL(
        'SELECT', 'SHEET', 
        where={'id_team': id_team, 'SHEET`.`id_file': id_file, 'user_id': user_id, 'conclusion': 0},
        where_especial={'start_date': 'IS NULL', 'end_date': 'IS NULL'},
        campo={'JOIN ON': ['PROJECT', 'id_file']},
        colunas_dados={
            'COUNT(*)': None
        }
    )

    nao_iniciadas = int(consulta[0].get('COUNT(*)', 0) or 0)

    consulta = consultaSQL(
        'SELECT', 'SHEET', 
        where={'id_team': id_team, 'SHEET`.`id_file': id_file, 'user_id': user_id,},
        where_especial={'conclusion': ['> 0', '< 1']},
        campo={'JOIN ON': ['PROJECT', 'id_file']},
        colunas_dados={
            'num': None,
            'start_date': None,
            'duration': None,
            'conclusion': None
        }
    )

    em_andamento = consulta

    progresso['total'] += total
    progresso['concluded'] += concluidas
    progresso['not_started'] += nao_iniciadas

    em_rows = rows_list(em_andamento)

    if em_rows:
        in_progress = len(em_rows)

        #print(f"Tarefas em andamento para o arquivo {id_file}: {in_progress}")

        overdue = calculate_delay(em_rows)
        overdue_count = 0

        for task in overdue:
            if task.get('atraso', 0) > 0:
                #print(f"\nTarefa: {task}\n")
                overdue_count += 1

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