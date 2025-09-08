from flask import Blueprint, request, jsonify, session
from dotenv import load_dotenv
from pathlib import Path
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
port = int(os.environ.get("PORT_DB"))
sid = os.environ.get("SID_DB")

print()
print(f"Usuário: {user}")
#print(f"Senha: {password}")
print(f"Host: {host}")
print(f"Port: {port}")
print(f"SID: {sid}")
print()

class Database:
    def __init__(self):
        pass

def conn(tipo, tabela, *where, **colunas_dados):
    try:
        # Estabelece a conexão
        connection = oracledb.connect(user=user, password=password, host=host, port=1521, sid="orcl")
        print("Conexão com o banco de dados Oracle estabelecida com sucesso!")

        cursor = connection.cursor() # Cria um cursor
        request_sql = "" # Armazena a string para consultar o banco de dados
        
        match tipo:
            case "INSERT":
                colunas = ", ".join(colunas_dados.keys())

                placeholders_list = []
                for chave in colunas_dados.keys():
                    placeholders_list.append(f":{chave}")
                placeholders = ", ".join(placeholders_list)

                #print(f"Placeholders: {placeholders}")
                
                """"
                No request_sql os placeholders (:user_id, :email...) são substituidos pelos valores
                sql_insert = INSERT INTO EMPREGADOS (ID, NOME, SALARIO) VALUES (:1, :2, :3)
                dados = (101, 'Ana', 5000.00)
                cursor.execute(sql_insert, dados)
                """

                request_sql = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
                cursor.execute(request_sql, colunas_dados) # Executa a solicitação no banco de dados
                
                connection.commit() # Commita as inserções

            case "SELECT":
                """SELECIONAR OS DADOS PARA AUTENTICAÇÃO
          RECEBER O EMAIL E SOLICITAR OS DADOS REFERENTE AO EMAIL"""

                colunas = ", ".join(colunas_dados.keys())

                request_sql = f"SELECT {colunas} FROM {tabela} WHERE {where[0]} = :valor"
                cursor.execute(request_sql, {'valor': where[1]})

                resultados = {}

                print("AQUI!")

                if tabela == "AUTH":
                    consulta = cursor.fetchone()
                    print(consulta)
                    if consulta:
                        print("AQUI!!!")
                        email = where[1]
                        user_dados = {}

                        for i, chave in enumerate(colunas_dados.keys()):
                            user_dados[chave] = consulta[i]
                        
                        resultados[email] = user_dados

                        print(resultados)
                        #print(f"Consulta: {consulta}")

                elif tabela == "METADATA":
                    consulta_resultados = cursor.fetchall()
                    
                    if consulta_resultados:
                        for consulta in consulta_resultados:
                            file_dados = {}

                            id_file = consulta[0]
                            file_dados['original_name'] = consulta[1]
                            file_dados['import_date'] = consulta[2]

                            file_dados['user_id'] = where[1]

                            resultados[id_file] = file_dados
                            
                            #print(f"Consulta: {consulta}")  
                
                #print(f"Resultado: {resultados}")

                return resultados

            case "UPDATE":
                pass
            case "DELETE":
                request_sql = f"DELETE FROM {tabela} WHERE {where[0]} = :valor"
                cursor.execute(request_sql, {'valor': where[1]})
                connection.commit()

        #print(f"Requisição: {request_sql}")
        #print(f"{cursor.rowcount} linha(s) modificada(s).")

    except oracledb.Error as error:
        print(f"Erro ao conectar ao banco de dados Oracle: {error}")
    finally:
        cursor.close()
        connection.close()
        print(f"Conexão encerrada.")


if __name__ == "__main__":
    conn("INSERT", "AUTH", 
    user_id =       '806443c5-9271-464a-a1da-4581c7f766e4', 
    email =         'usuario@empresa.com.br',
    password_hash = '123456',
    name =          'Iury',
    last_name =     'Cardoso',
    role =          'admin')

    print("\n\n")

    conn("SELECT", "AUTH", 
    'email', 'usuario@empresa.com.br', 
    user_id=None, 
    password_hash=None,
    name=None,
    last_name=None,
    role=None)
    """
    print("\n\n")
    """

    """conn("INSERT", "METADATA", 
    id_file='a90f460d-b8f6-4a5c-978e-45513cfae20b',
    original_name='Desafio_Numero_1_Projeto_8_-_Exportado.xlsx',
    import_date='06-09-2025 21:55:00',
    AUTH_user_id='806443c5-9271-464a-a1da-4581c7f766e4')

    print("\n\n")

    conn("SELECT", "METADATA",
    'auth_user_id', '806443c5-9271-464a-a1da-4581c7f766e4',
    id_file=None,
    original_name=None,
    import_date=None
    )"""