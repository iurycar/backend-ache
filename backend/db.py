from flask import Blueprint, request, jsonify, session
from dotenv import load_dotenv
from pathlib import Path
import mysql.connector
import oracledb
import os

"""
    Esse arquivo lidará com as requisições do frontend e backend para o banco de dados
    Deverá conectar ao banco de dados e fazer consultas, como por exemplo SELECT * FROM auth
"""

load_dotenv()
user = os.environ.get("USER_DB")
password = os.environ.get("PASSWORD_DB")
host = os.environ.get("HOST_DB")
port = os.environ.get("PORT_DB")
database = os.environ.get("DATABASE")

print()
print(f"Usuário: {user}")
#print(f"Senha: {password}")
print(f"Host: {host}")
print(f"Nome do DB: {database}")
print()

class Database:
    def __init__(self):
        pass

def conn(tipo, tabela, *where, **colunas_dados):
    try:
        # Estabelece a conexão
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database
        )
        print("\nConexão com o banco de dados MySQL estabelecida com sucesso!")

        tabela = tabela.upper()

        cursor = connection.cursor(dictionary=True) # Cria um cursor
        request_sql = "" # Armazena a string para consultar o banco de dados
        
        match tipo:
            case "INSERT":
                # Transforma os valores do dicionário para uma tupla que o MySQL entende
                # (1, 'adasd', ...)
                dados = tuple(colunas_dados.values())

                colunas = ", ".join(colunas_dados.keys())
                placeholders = ", ".join(["%s"] * len(colunas_dados))  
                #print(f"Placeholders: {placeholders}")
                print(f"Valores inseridos: {dados}")

                request_sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
                
                

                cursor.execute(request_sql, dados) # Executa a solicitação no banco de dados
                connection.commit() # Commita as inserções
                print("INSERT bem-sucedido!")
                
            case "SELECT":
                """SELECIONAR OS DADOS PARA AUTENTICAÇÃO
          RECEBER O EMAIL E SOLICITAR OS DADOS REFERENTE AO EMAIL"""

                colunas = ", ".join(colunas_dados.keys())

                request_sql = f"SELECT {colunas} FROM {tabela} WHERE {where[0]} = %s"
                cursor.execute(request_sql, (where[1],))

                resultados = {}

                if tabela == "AUTH":
                    consulta = cursor.fetchone()
                    email = where[1]
                    user_dados = {}

                    if consulta:
                        #print(f"Consulta: {consulta}")
                        resultados[email] = consulta

                elif tabela == "METADATA":
                    consulta_resultados = cursor.fetchall()
                    #print(consulta_resultados)

                    if consulta_resultados:
                        for consulta in consulta_resultados:
                            file_id = consulta['id_file']
                            resultados[file_id] = consulta
                            #print(f"\nConsulta: {consulta}")  
                            #print(f"\nResultado: {resultados}")
                
                #print(f"Resultado: {resultados}")

                return resultados

            case "UPDATE":
                pass
            case "DELETE":
                request_sql = f"DELETE FROM {tabela} WHERE {where[0]} = %s"
                cursor.execute(request_sql, (where[1],))
                connection.commit()
                print("DELETE bem-sucedido!")

        #print(f"Requisição: {request_sql}")
        #print(f"{cursor.rowcount} linha(s) modificada(s).")

    except oracledb.Error as error:
        print(f"Erro ao conectar ao banco de dados MySQL: {error}")
        # Caso tenha uma conexão com o banco de dados, dá rollback para não afetar os dados
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print(f"Conexão encerrada.")


if __name__ == "__main__":
    """conn("INSERT", "AUTH", 
    user_id =       '806443c5-9271-464a-a1da-4581c7f766e4', 
    email =         'usuario@empresa.com.br',
    password_hash = '123456',
    name =          'Iury',
    last_name =     'Cardoso',
    role =          'admin')
    
    print("")

    auth_data = conn("SELECT", "AUTH", 
    'email', 'usuario@empresa.com.br', 
    user_id=None, 
    password_hash=None,
    name=None,
    last_name=None,
    role=None)
    
    print(f"\nResultado da consulta AUTH: {auth_data}\n")"""

    conn("DELETE", "METADATA", '1', '1')

    """conn("INSERT", "METADATA", 
    id_file='a90f460d-b8f6-4a5c-978e-45513cfae20b',
    original_name='Desafio_Numero_1_Projeto_8_-_Exportado.xlsx',
    import_date='2025-09-06T23:07:08.056656',
    AUTH_user_id='806443c5-9271-464a-a1da-4581c7f766e4')"""

    print("")
    
    metadata_data = conn("SELECT", "METADATA",
    'auth_user_id', '806443c5-9271-464a-a1da-4581c7f766e4',
    id_file=None,
    original_name=None,
    import_date=None,
    auth_user_id=None
    )

    print(f"\nResultado da consulta METADATA: {metadata_data}\n")