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


def get_progress(id_file: str, id_team: str, user_id: str = None) -> dict:

    progresso = {
        'total': 0,
        'concluded': 0,
        'not_started': 0,
        'in_progress': 0,
        'overdue': 0
    }

    # Se id_file for 'all' ou vazio, então pegar o progresso de todos os projetos ativos do time
    all_projects = (not id_file) or (id_file.strip() == '') or (id_file == None) or (id_file.lower() == 'null')

    if all_projects:

        if user_id is None:
            consulta_projetos: dict[dict] = consultaSQL(
                'SELECT', 'PROJECT', 
                where={'id_team': id_team},
                colunas_dados={
                    'id_file': None,
                    'completed': None,
                    'project_name': None
                }
            )
        else:
            consulta_projetos: dict[dict] = consultaSQL(
                'SELECT', 'PROJECT', 
                where={'id_team': id_team, 'user_id': user_id},
                colunas_dados={
                    'id_file': None,
                    'completed': None,
                    'project_name': None
                }
            )

        if not consulta_projetos:
            return None

        # consulta_projetos é um dicionário onde a chave é o id_file e o valor é outro dicionário com os dados do projeto
        # Exemplo: {'proj1': {'id_file': 'proj1', 'completed': 0, 'project_name': 'Projeto 1'}, ...}
        #print(f"\nProjetos ativos encontrados para o time {id_team}: {consulta_projetos}\n")

        # Para cada projeto, calcular o progresso
        for id_projeto, projeto in consulta_projetos.items():
            pid = projeto.get('id_file') # Pega o id_file do projeto
            
            if not pid:
                continue

            # Se o projeto já estiver concluído, então todas as tarefas estão concluídas
            if int(projeto.get('completed', 0) or 0) == 1:
                consulta_tarefas: list[dict] = consultaSQL(
                    'SELECT', 'SHEET', 
                    where={'id_file': pid},
                    campo={'COUNT': '*'}
                )
                
                if consulta_tarefas:
                    total = int(consulta_tarefas[0].get('COUNT(*)', 0) or 0)
                    progresso['total'] += total
                    progresso['concluded'] += total
                continue

            # Se o projeto não estiver concluído, calcular o progresso normalmente
            progresso = calculate_progress(projeto['id_file'], progresso, user_id)

    else: 
        # Se o id_file foi fornecido, então pega o progresso somente daquele projeto
        consulta_projeto: list[dict] = consultaSQL(
            'SELECT', 'PROJECT', 
            where={'id_team': id_team, 'id_file': id_file},
            colunas_dados={
                'completed': None,
                'id_file': None,
                'project_name': None
            }
        )

        if not consulta_projeto:
            return None

        print(f"Projeto ativo encontrado para o time {id_team}: {consulta_projeto}")

        # Se o projeto já estiver concluído, então todas as tarefas estão concluídas
        if int(consulta_projeto[id_file].get('completed', 0)) == 1:
            consulta_tarefas: list[dict] = consultaSQL(
                'SELECT', 'SHEET', 
                where={'id_file': id_file},
                campo={'COUNT': '*'}
            )
            
            if consulta_tarefas:
                progresso['total'] += consulta_tarefas[0].get('COUNT(*)', 0)
                progresso['concluded'] += consulta_tarefas[0].get('COUNT(*)', 0)
        else:
            progresso = calculate_progress(id_file, progresso, user_id)

    return progresso


def calculate_progress(id_file: str, progress: dict, user_id: str) -> dict:

    if user_id:
        consulta_tarefas: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file, 'user_id': user_id}, 
            campo={'COUNT': '*'}
        )

        concluidas: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file, 'user_id': user_id, 'conclusion': 1}, 
            campo={'COUNT': '*'},
        )

        nao_iniciadas: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file, 'user_id': user_id, 'conclusion': 0},
            campo={'COUNT': '*'},
        )

        em_andamento: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file, 'user_id': user_id},
            where_especial={'conclusion': '> 0', 'conclusion': '< 1'},
        )

    else:
        consulta_tarefas: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file}, 
            campo={'COUNT': '*'}
        )

        concluidas: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file, 'conclusion': 1}, 
            campo={'COUNT': '*'},
        )        

        nao_iniciadas: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file, 'conclusion': 0},
            campo={'COUNT': '*'},
        )        

        em_andamento: list[dict] = consultaSQL(
            'SELECT', 'SHEET', 
            where={'id_file': id_file},
            where_especial={'conclusion': '> 0', 'conclusion': '< 1'},
        )   

    if consulta_tarefas:
        progress['total'] += int(consulta_tarefas[0].get('COUNT(*)', 0) or 0)

    if nao_iniciadas:
        progress['not_started'] += int(nao_iniciadas[0].get('COUNT(*)', 0) or 0)

    if concluidas:
        progress['concluded'] += int(concluidas[0].get('COUNT(*)', 0) or 0)

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