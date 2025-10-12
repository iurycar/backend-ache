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

        dt_valor = row.get('start_date')

        if not dt_valor or dt_valor == '' or dt_valor is None:
            row['atraso'] = 0
            row['start_date'] = None
            continue

        #print(f"Duração original para linha {row.get('num')}: {row.get('duration')}")

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

        #print(f"Calculando atraso para linha {row.get('num')}:")
        #print(f"  Data de início: {dt_inicio}")
        #print(f"  Data atual: {dt_hoje}")
        #print(f"  Duração (dias): {dias}")
        #print(f"  Data de fim calculada: {prazo}")

        #print(f"Atraso calculado para linha {row.get('num')}: {atraso} dias")
        
        row['atraso'] = atraso
        row['start_date'] = row['start_date'].isoformat()

    return data

def calculate_progress(id_file: str, progress: dict) -> dict:
    consulta_tarefas: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, "COUNT(*)")

    if consulta_tarefas:
        progress['total'] += int(consulta_tarefas[0].get('COUNT(*)', 0) or 0)

    concluidas: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'CONCLUDED')

    if concluidas:
        progress['concluded'] += int(concluidas[0].get('COUNT(*)', 0) or 0)

    nao_iniciadas: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'NOT_STARTED')

    if nao_iniciadas:
        progress['not_started'] += int(nao_iniciadas[0].get('COUNT(*)', 0) or 0)

    em_andamento: list[dict] = consultaSQL('SELECT', 'SHEET', 'id_file', id_file, 'IN_PROGRESS')
    em_rows = rows_list(em_andamento)

    if em_rows:
        in_progress = len(em_rows)

        #print(f"Tarefas em andamento para o arquivo {id_file}: {in_progress}")

        overdue = calculate_delay(em_rows)
        overdue_count = 0

        for task in overdue:
            #print(f"\nTarefa: {task}\n")
            if task.get('atraso', 0) > 0:
                overdue_count += 1

        in_progress_count = max(in_progress - overdue_count, 0)

        progress['in_progress'] += in_progress_count
        progress['overdue'] += overdue_count

    return progress

def rows_list(result) -> list[dict]:
    if isinstance(result, dict):
        return list(result.values())
    if isinstance(result, list):
        return result
    return []