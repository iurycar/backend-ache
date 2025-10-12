from flask import Blueprint, request, jsonify, session
from sqlalchemy import create_engine
from dotenv import load_dotenv
from string import Template
import mysql.connector
import datetime
import os

"""
    Esse arquivo lidará com as requisições do frontend e backend para o banco de dados
    Deverá conectar ao banco de dados e fazer consultas, como por exemplo SELECT * FROM employee
"""

load_dotenv()
user = os.environ.get("USER_DB")
password = os.environ.get("PASSWORD_DB")
host = os.environ.get("HOST_DB")
port = os.environ.get("PORT_DB")
database = os.environ.get("DATABASE")

db_url = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
ENGINE = create_engine(db_url)

class Database:
    def __init__(self):
        pass

def consultaSQL(tipo: str, tabela: str, *where: str, **colunas_dados: str) -> dict | None:
    """
    Função para consultas SQL no banco de dados.

    @param tipo: Tipo de consulta - "INSERT", "SELECT", "UPDATE", "DELETE"

    @param tabela: Nome da tabela no banco de dados

    @param where: Parâmetros para cláusula WHERE (ex. 'id', '1', 'name', 'John' => WHERE id='1' AND name='John')

    @param colunas_dados: Colunas e seus valores para INSERT ou UPDATE (ex. id='1', name='John')
    
    @return: Dicionário com os resultados da consulta ou None
    """

    if tipo not in ["INSERT", "SELECT", "UPDATE", "DELETE"]:
        raise ValueError("Tipo de consulta inválido. Use 'INSERT', 'SELECT', 'UPDATE' ou 'DELETE'.")
        
    try:
        # Estabelece a conexão
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database
        )

        tabela = tabela.upper()
        params: tuple = () # Parâmetros para consultas SQL
        resultados: dict = {}

        cursor = connection.cursor(dictionary=True) # Cria um cursor
        
        match tipo:
            case "INSERT":
                # Transforma os valores do dicionário para uma tupla que o MySQL entende
                # (1, 'adasd', ...)
                dados = tuple(colunas_dados.values())

                colunas_list: list[str] = []
                for chave in colunas_dados.keys():
                    colunas_list.append(f"`{chave}`")

                colunas = ", ".join(colunas_list)
                placeholders = ", ".join(["%s"] * len(colunas_dados))  
                #print(f"Placeholders: {placeholders}")
                #print(f"Valores inseridos: {dados}")

                # Cria a query SQL usando Template para evitar SQL Injection
                template_sql_query = Template("INSERT INTO `$tabela` ($colunas) VALUES ($placeholders)")
                sql_query = template_sql_query.safe_substitute(tabela=tabela, colunas=colunas, placeholders=placeholders)

                #print(f"SQL Query: {sql_query} -> {dados}")

                cursor.execute(sql_query, dados) # Executa a solicitação no banco de dados
                connection.commit() # Commita as inserções
                print(f"INSERT em {tabela} bem-sucedido!")
                
            case "SELECT":
                if len(where) >= 2 and len(where) % 2 == 0:
                    colunas = ", ".join(colunas_dados.keys())

                    where_parts: list[str] = []
                    valores_where: list[object] = []

                    # Monta WHERE com pares (coluna, valor)
                    for i in range(0, len(where), 2):
                        # Obtém a coluna e o valor (ex. id_file = '1')
                        where_coluna = str(where[i])
                        where_valor = where[i + 1]
                        
                        where_parts.append(f"`{where_coluna}` = %s")
                        valores_where.append(where_valor)

                    # Monta a cláusula WHERE (ex. `id_file` = %s AND `name` = %s)
                    where_clause = " AND ".join(where_parts)

                    template_sql_query = Template("SELECT $colunas from `$tabela` WHERE $where_clause")
                    sql_query = template_sql_query.safe_substitute(colunas=colunas, tabela=tabela, where_clause=where_clause)

                    # Monta os parâmetros da consulta
                    params = tuple(valores_where)
                    
                    #print(f"SQL Query: {sql_query} -> {params}")

                elif len(where) != 1 and len(where) % 2 != 0:
                    match where[2]:
                        case "MAX(num)":
                            template_sql_query = Template("SELECT MAX(num) FROM `$tabela` WHERE $where_coluna = %s")
                        case "MAX(completed_projects)":
                            template_sql_query = Template("SELECT MAX(completed_projects) FROM `$tabela` WHERE $where_coluna = %s")
                        case "MAX(in_progress)":
                            template_sql_query = Template("SELECT MAX(in_progress) FROM `$tabela` WHERE $where_coluna = %s")
                        case "COUNT(*)":
                            template_sql_query = Template("SELECT COUNT(*) FROM `$tabela` WHERE $where_coluna = %s")
                        case "CONCLUDED":
                            template_sql_query = Template("SELECT COUNT(*) FROM `$tabela` WHERE $where_coluna = %s AND conclusion = 1")
                        case "NOT_STARTED":
                            template_sql_query = Template("SELECT COUNT(*) FROM `$tabela` WHERE $where_coluna = %s AND start_date IS NULL")
                        case "IN_PROGRESS":
                            template_sql_query = Template("SELECT `start_date`, `duration`, `conclusion` FROM `$tabela` WHERE $where_coluna = %s AND start_date IS NOT NULL AND conclusion < 1")
                        case _:
                            pass
                    
                    if template_sql_query:
                        sql_query = template_sql_query.safe_substitute(tabela=tabela, where_coluna=where[0])
                        #print(f"SQL Query: {sql_query} -> %s: {where[1]}")
                        params = (where[1],)

                elif len(where) == 1:
                    template_sql_query = Template("SELECT * from `$tabela`")
                    sql_query = template_sql_query.safe_substitute(tabela=tabela)
                    params = ()
                else:
                    raise ValueError("Parâmetros WHERE inválidos para SELECT.")

                cursor.execute(sql_query, params)

                if tabela == "EMPLOYEE":
                    if len(where) >= 2 and str(where[0]).lower() == "email":
                        consulta = cursor.fetchone() # Pega o primeiro resultado da consulta
                        email: str = where[1]

                        if consulta:
                            #print(f"Consulta: {consulta}")
                            resultados[email] = consulta
                        return resultados
                    
                    consulta_resultados = cursor.fetchall() # Pega todos os resultados da consulta
                    #print(consulta_resultados)
                    if consulta_resultados:
                        return consulta_resultados

                elif tabela == "PROJECT":
                    consulta_resultados = cursor.fetchall() # Pega todos os resultados da consulta
                    #print(consulta_resultados)

                    if consulta_resultados:
                        if 'id_file' in consulta_resultados[0]:
                            for consulta in consulta_resultados:
                                file_id = consulta['id_file']
                                resultados[file_id] = consulta
                            return resultados
                        else:
                            return consulta_resultados

                elif tabela == "SHEET":
                    consulta_resultados = cursor.fetchall()
                    return consulta_resultados
                #print(f"Resultado: {resultados}")

                elif tabela == "TEAMS":
                    consulta = cursor.fetchone() # Pega o primeiro resultado da consulta
                    if consulta:
                        return consulta
                
                elif tabela == "TASK_HISTORY":
                    consulta_resultados = cursor.fetchall() # Pega todos os resultados da consulta
                    return consulta_resultados

                #resultados = cursor.fetchall() # Pega todos os resultados da consulta
                return resultados

            case "UPDATE":
                if not colunas_dados:
                    raise ValueError("Nenhuma coluna para atualizar foi informada.")

                # Monta WHERE com pares (coluna, valor)
                if len(where) == 0 or len(where) % 2 != 0:
                    raise ValueError("Parâmetros WHERE inválidos para UPDATE.")

                where_parts: list[str] = []         # Partes do WHERE
                valores_where: list[object] = []    # Valores para o WHERE

                # Inicia em 0 e vai até len(where) em passos de 2
                # Dessa forma, pega os pares (coluna, valor)
                for i in range(0, len(where), 2):
                    where_coluna = str(where[i])
                    where_valor = where[i + 1]
                    where_parts.append(f"`{where_coluna}` = %s")
                    valores_where.append(where_valor)

                if 'start_date' in colunas_dados and colunas_dados['start_date'] == 'NOW()':
                    where_parts.append('(`start_date` IS NULL)')
                if 'conclusion' in colunas_dados and colunas_dados['conclusion'] == '> 0 AND < 1':
                    where_parts.append('(`conclusion` > 0 AND `conclusion` < 1)')
                    del colunas_dados['conclusion']

                if 'end_date' in colunas_dados and colunas_dados['end_date'] == 'NOW()':
                    where_parts.append('(`end_date` IS NULL)')

                # Monta SET: `col` = %s
                set_cols: str = ", ".join([f"`{col}` = %s" for col in colunas_dados.keys()])

                where_clause: str = " AND ".join(where_parts)

                template_sql_query = Template("UPDATE `$tabela` SET $set_cols WHERE $where_clause")
                sql_query = template_sql_query.safe_substitute(tabela=tabela, set_cols=set_cols, where_clause=where_clause)

                colunas: tuple = ()
                # Valores do SET
                for valor in colunas_dados.values():
                    if valor != '> 0 AND < 1':
                        if valor == 'NOW()':
                            colunas += (datetime.datetime.now(),)
                        else:
                            colunas += (valor,)

                # Valores: primeiro os do SET, depois os do WHERE
                params = colunas + tuple(valores_where)
                cursor.execute(sql_query, params)
                connection.commit()
                print(f"UPDATE {tabela} bem-sucedido! {cursor.rowcount} linha(s) afetada(s).")
                return {"linhas_afetadas": cursor.rowcount}

            case "DELETE":
                # Evitar que de alguma forma coloque * ou sem WHERE e apague tudo :/
                if len(where) < 2 or len(where) % 2 != 0:
                    raise ValueError("Parâmetros WHERE inválidos para DELETE.")
                
                # Monta WHERE com pares (coluna, valor)
                if len(where) == 2:
                    template_sql_query = Template("DELETE FROM `$tabela` WHERE $where_coluna = %s")
                    sql_query = template_sql_query.safe_substitute(tabela=tabela, where_coluna=where[0])
                    params = (where[1],)
                    
                elif len(where) > 2 and len(where) % 2 == 0:
                    where_parts: list[str] = []
                    valores_where: list[object] = []

                    for i in range(0, len(where), 2):
                        where_coluna = str(where[i])
                        where_valor = where[i + 1]
                        where_parts.append(f"`{where_coluna}` = %s")
                        valores_where.append(where_valor)

                    where_clause = " AND ".join(where_parts)

                    template_sql_query = Template("DELETE FROM `$tabela` WHERE $where_clause")
                    sql_query = template_sql_query.safe_substitute(tabela=tabela, where_clause=where_clause)
                    params = tuple(valores_where)
                
                cursor.execute(sql_query, params)
                connection.commit()
                print(f"DELETE {tabela} : {params} bem-sucedido!")

        #print(f"Requisição: {sql_query}")
        #print(f"{cursor.rowcount} linha(s) modificada(s).")

    except Exception as error:
        print(f"Erro ao conectar ao banco de dados MySQL: {error}")
        # Caso tenha uma conexão com o banco de dados, dá rollback para não afetar os dados
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        #print(f"Conexão encerrada.")


if __name__ == "__main__":
    consultaSQL()

    """consultaSQL("INSERT", "EMPLOYEE", 
    user_id =       '806443c5-9271-464a-a1da-4581c7f766e4', 
    email =         'usuario@empresa.com.br',
    password_hash = '123456',
    name =          'Iury',
    last_name =     'Cardoso',
    role =          'admin')
    
    print("")

    auth_data = consultaSQL("SELECT", "EMPLOYEE", 
    'email', 'usuario@empresa.com.br', 
    user_id=None, 
    password_hash=None,
    name=None,
    last_name=None,
    role=None)
    
    print(f"\nResultado da consulta EMPLOYEE: {auth_data}\n")

    consultaSQL("DELETE", "METADATA", '1', '1')

    consultaSQL("INSERT", "METADATA", 
    id_file='a90f460d-b8f6-4a5c-978e-45513cfae20b',
    original_name='Desafio_Numero_1_Projeto_8_-_Exportado.xlsx',
    import_date='2025-09-06T23:07:08.056656',
    AUTH_user_id='806443c5-9271-464a-a1da-4581c7f766e4')

    print("")
    
    metadata_data = consultaSQL("SELECT", "METADATA",
    'auth_user_id', '806443c5-9271-464a-a1da-4581c7f766e4',
    id_file=None,
    original_name=None,
    import_date=None,
    auth_user_id=None
    )

    print(f"\nResultado da consulta METADATA: {metadata_data}\n")

    id_file = 'bd01523e-d4fd-47f8-9a07-cae35366b15f.xlsx'
    sheet_data = consultaSQL('SELECT', 'SHEET', 'METADATA_id_file', id_file,
    num=None,
    classe=None,
    category=None,
    phase=None,
    status=None,
    name=None,
    duration=None,
    text=None,
    reference=None,
    conclusion=None)
    print(sheet_data)"""