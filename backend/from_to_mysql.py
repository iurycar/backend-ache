from .db import conn, engine
from pathlib import Path
import pandas as pd

diretorio = Path(__file__).parent
path = diretorio / "uploads" 

def to_mysql_inserir(id_file):
    try:
        file_path = path / id_file
    
        sheet = pd.read_excel(file_path)

        sheet['METADATA_id_file'] = id_file

        sheet.rename(columns={
            'Número': 'num',
            'Classificação': 'classe',
            'Categoria': 'category',
            'Fase': 'phase',
            'Condição': 'status',
            'Nome': 'name',
            'Duração': 'duration',
            'Como Fazer': 'text',
            'Documento Referência': 'reference',
            '% Concluída': 'conclusion'
        }, inplace=True)

        print("Iniciando a inserção na tabela SHEET...")
        sheet.to_sql(
            'sheet',
            con=engine,
            if_exists='append',
            index=False
        )
        
        print(f"Dados inseridos com sucesso na tabela SHEET.")
    except Exception as error:
        print(f"Erro ao inserir os dados do arquivo para o MySQL: {error}")


def from_mysql_extrair(id_file):
    try:
        file_path = path / id_file

        colunas = {
            'num': 'Número',
            'classe': 'Classificação',
            'category': 'Categoria',
            'phase': 'Fase',
            'status': 'Condição',
            'name': 'Nome',
            'duration': 'Duração',
            'text': 'Como Fazer',
            'reference': 'Documento Referência',
            'conclusion': '% Concluída',
            'METADATA_id_file': 'ID do Arquivo'
        }

        sql_query = f"SELECT `num`,`classe`,`category`,`phase`,`status`,`name`,`duration`,`text`,`reference`,`conclusion` FROM `sheet` WHERE `METADATA_id_file` = '{id_file}'"

        print(f"Buscando dados na tabela SHEET para o arquivo '{id_file}'.")

        sheet = pd.read_sql(sql_query, con=engine)

        if sheet.empty:
            print("Nenhum dado encontrado para o arquivo solicitado.")
            return
        
        sheet.rename(columns=colunas, inplace=True)

        if 'index' in sheet.columns:
            sheet.drop(columns=['index'], inplace=True)

        sheet.to_excel(file_path, index=False)

        print(f"Dados exportados com sucesso para o arquivo '{id_file}'.")
    except Exception as error:
        print(f"Erro ao extrair os dados do MySQL para o arquivo: {error}")

if __name__ == '__main__':
    user_id = "806443c5-9271-464a-a1da-4581c7f766e4"
    id_file = "f9316b87-29f1-4a4b-a123-40b4517a3721.xlsx"
    filename = "Desafio Número 1_Projeto 6 - Exportado.xlsx"

    """to_mysql_inserir(id_file, filename, user_id)"""

    from_mysql_extrair(id_file)
        