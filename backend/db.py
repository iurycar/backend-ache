from flask import Blueprint, request, jsonify, session
from sqlalchemy import create_engine
from dotenv import load_dotenv
from string import Template
from typing import Any
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

def consultaSQL(tipo: str, tabela: str, where: dict[str, Any] = None, colunas_dados: dict[str, Any] = {}, campo: dict[str, str | int] = None, where_especial: dict[str, str | list] = None) -> dict | None:
    """
    Função para consultas SQL no banco de dados.

    @param tipo: Tipo de consulta - "INSERT", "SELECT", "UPDATE", "DELETE"
    @param tabela: Nome da tabela no banco de dados
    @param where: Parâmetros para cláusula WHERE (ex. {'id': '1', 'name': 'John'} => WHERE id='1' AND name='John')
    @param colunas_dados: Colunas e seus valores para INSERT ou UPDATE (ex. {'id': '1', 'name': 'John'}), para SELECT pode ser vazio {'id': None, 'name': None}
    @param campo: Campo especial para SELECT, como "MAX()" e "COUNT()" (ex. {'MAX': 'id'} ou {'COUNT': '*'})
    @param where_especial: Condições especiais para a cláusula WHERE (ex. {'start_date': 'IS NULL', 'conclusion': '> 0'} -> WHERE start_date IS NULL AND conclusion > 0)

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
                colunas_where: list[str] = []
                valores_where: tuple[object] = ()
                colunas: str = '*'

                if colunas_dados not in [None, {}]:
                    colunas = ", ".join(colunas_dados.keys()) 

                # Monta WHERE com pares (coluna, valor)
                for coluna, valor in where.items():
                    # Obtém a coluna e o valor (ex. id_file = '1')
                    if valor != '':
                        colunas_where.append(f"`{str(coluna)}` = %s")
                        valores_where += (valor,)

                # Se houver parâmetros especiais, adiciona ao WHERE
                if where_especial:
                    # Exemplo: {'start_date': 'IS NULL', 'conclusion': ['> 0', '< 1']}
                    # Converte para 'start_date IS NULL AND conclusion > 0 AND conclusion < 1'
                    for coluna, valor in where_especial.items():
                        if isinstance(valor, list): 
                            # Se for uma lista, adiciona cada condição
                            # Exemplo: {'conclusion': ['> 0', '< 1']}
                            # Converte para 'conclusion > 0 AND conclusion < 1'
                            for v in valor:
                                colunas_where.append(f"`{str(coluna)}` {v}")
                        else:
                            colunas_where.append(f"`{str(coluna)}` {valor}")

                # Monta a cláusula WHERE (ex. `id_file` = %s AND `name` = %s)
                where_clause = " AND ".join(colunas_where) if colunas_where else '1=1'

                # Cria a query SQL usando Template para evitar SQL Injection
                if campo:
                    # Obtém a chave e o valor do campo especial
                    # Exemplo: {'MAX': 'num'} ou {'COUNT': '*'} ou {'JOIN ON': ['tabela2', 'coluna']}
                    chave, valor = list(campo.items())[0]
                    
                    if isinstance(valor, list):
                        tabela_join, coluna_join = valor
                        
                        # SELECT col1, col2 FROM tabela JOIN tabela2 ON tabela.col = tabela2.col WHERE ...
                        template_sql_query = Template("SELECT $colunas FROM `$tabela` JOIN `$tabela_join` ON `$tabela`.`$coluna_join` = `$tabela_join`.`$coluna_join` WHERE $where_clause")
                        sql_query = template_sql_query.safe_substitute(colunas=colunas, tabela=tabela, tabela_join=tabela_join, coluna_join=coluna_join, where_clause=where_clause)
                        params = tuple(valores_where)
                        print(f"\nSQL Query: {sql_query} -> {params}")
                    else:
                        template_sql_query = Template("SELECT $campo($coluna) FROM `$tabela` WHERE $where_clause")
                        sql_query = template_sql_query.safe_substitute(campo=chave, coluna=valor, tabela=tabela, where_clause=where_clause)
    
                else:
                    template_sql_query = Template("SELECT $colunas from `$tabela` WHERE $where_clause")
                    sql_query = template_sql_query.safe_substitute(colunas=colunas, tabela=tabela, where_clause=where_clause)

                # Monta os parâmetros da consulta
                params = tuple(valores_where)
                #print(f"\nSQL Query: {sql_query} -> {params}")

                cursor.execute(sql_query, params)

                if tabela == "EMPLOYEE":
                    if (where.get('email') is not None) and (len(where) == 2):
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

                    # Se houver resultados, organiza por id_file
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

                #resultados = cursor.fetchall() # Pega todos os resultados da consulta
                return resultados

            case "UPDATE":
                if not colunas_dados:
                    raise ValueError("Nenhuma coluna para atualizar foi informada.")

                colunas_where: list[str] = []         # Partes do WHERE
                valores_where: list[object] = []    # Valores para o WHERE
                colunas_set: list[str] = []         # Partes do SET
                valores_set: tuple[str] = ()        # Valores para o SET

                # -> WHERE `coluna` = %s AND `coluna2` = %s ...
                # Monta WHERE com pares (coluna, valor)
                for coluna, valor in where.items():
                    colunas_where.append(f"`{coluna}` = %s")
                    valores_where.append(valor)

                # Se houver parâmetros especiais, adiciona ao WHERE
                if where_especial:
                    for coluna, valor in where_especial.items():
                        if isinstance(valor, list):
                            for v in valor:
                                colunas_where.append(f"`{str(coluna)}` {v}")
                        else:
                            colunas_where.append(f"`{str(coluna)}` {valor}")
                            
                where_clause: str = " AND ".join(colunas_where)

                # -> SET `coluna` = %s, `coluna2` = %s ...
                # Monta SET com pares (coluna, valor)
                for coluna, valor in colunas_dados.items():
                    colunas_set.append(f"`{coluna}` = %s")
                    valores_set += (valor,)

                colunas_set_str: str = ", ".join(colunas_set)

                template_sql_query = Template("UPDATE `$tabela` SET $set_colunas WHERE $where_clause")
                sql_query = template_sql_query.safe_substitute(tabela=tabela, set_colunas=colunas_set_str, where_clause=where_clause)

                # Valores: primeiro os do SET, depois os do WHERE
                params = valores_set + tuple(valores_where)
                print(f"\nSQL Query: {sql_query} -> {params}\n")
                cursor.execute(sql_query, params)
                connection.commit()
                print(f"UPDATE {tabela} bem-sucedido! {cursor.rowcount} linha(s) afetada(s).")
                return {"linhas_afetadas": cursor.rowcount}

            case "DELETE":               
                # Monta WHERE com pares (coluna, valor)
                colunas_where: list[str] = []
                valores_where: list[object] = []

                for coluna, valor in where.items():
                    colunas_where.append(f"`{coluna}` = %s")
                    valores_where.append(valor)

                where_clause = " AND ".join(colunas_where)

                template_sql_query = Template("DELETE FROM `$tabela` WHERE $where_clause")
                sql_query = template_sql_query.safe_substitute(tabela=tabela, where_clause=where_clause)
                params = tuple(valores_where)
                
                print(f"SQL Query: {sql_query} -> {params}")

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