from flask import Blueprint, request, jsonify, session
from sqlalchemy import create_engine
from dotenv import load_dotenv
from string import Template
import mysql.connector
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

def consultaSQL(tipo: "Tipo de consulta", tabela: "Nome da tabela", *where: "2 args - ex. id = '1'", **colunas_dados: "Colunas desejadas") -> dict | None:
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

                cursor.execute(sql_query, dados) # Executa a solicitação no banco de dados
                connection.commit() # Commita as inserções
                print(f"INSERT em {tabela} bem-sucedido!")
                
            case "SELECT":
                colunas = ", ".join(colunas_dados.keys())

                template_sql_query = Template("SELECT $colunas FROM `$tabela` WHERE $where_coluna = %s")
                sql_query = template_sql_query.safe_substitute(colunas=colunas, tabela=tabela, where_coluna=where[0])
                #print(f"SQL Query: {sql_query}")

                cursor.execute(sql_query, (where[1],))

                resultados = {}

                if tabela == "EMPLOYEE":
                    consulta = cursor.fetchone()
                    email: str = where[1]

                    if consulta:
                        #print(f"Consulta: {consulta}")
                        resultados[email] = consulta

                elif tabela == "PROJECT":
                    consulta_resultados = cursor.fetchall()
                    #print(consulta_resultados)

                    if consulta_resultados:
                        for consulta in consulta_resultados:
                            file_id = consulta['id_file']
                            resultados[file_id] = consulta
                            #print(f"\nConsulta: {consulta}")  
                            #print(f"\nResultado: {resultados}")
                
                elif tabela == "SHEET":
                    consulta_resultados = cursor.fetchall()
                    return consulta_resultados
                #print(f"Resultado: {resultados}")

                return resultados

            case "UPDATE":
                pass
            case "DELETE":
                template_sql_query = Template("DELETE FROM `$tabela` WHERE $where_coluna = %s")
                sql_query = template_sql_query.safe_substitute(tabela=tabela, where_coluna=where[0])
                cursor.execute(sql_query, (where[1],))
                connection.commit()
                print(f"DELETE {tabela} : {where[1]} bem-sucedido!")

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
    #consultaSQL()

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