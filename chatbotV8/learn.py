from pathlib import Path
import json

diretorio = Path(__file__).parent
caminho_termo = diretorio / "dados" / "termos_chaves.json"
caminho_resposta = diretorio / "dados" / "respostas.json"

def get_keywords() -> dict[str, list[str]]:
    """ Função para acessar os dados treinados para perguntas no arquivo termos_chaves.json.
    @return: Dicionário com palavras chaves e suas respectivas demandas."""
    # Verifica se o arquivo existe
    if caminho_termo.exists():
        palavras_chave: dict[str, list[str]] = {}

        # Abre o arquino modo leitura e utiliza o sistema de codificação de caracteres "utf-8"
        with open(caminho_termo, "r", encoding="utf-8") as termos:
            palavras_chave = json.load(termos)

        return palavras_chave

    else:
        print(f"Erro: O arquivo '{caminho_termo}' não encontrado.")

def get_response_keywords() -> dict[str, str | int]:
    """ Função para acessar os dados treinados para respostas no arquivo respostas.json.
    @return: Dicionário com demandas e suas respectivas respostas."""
    
    # Verifica se o arquivo existe
    if caminho_resposta.exists():
        responder_chaves: dict[str, str | int] = {}

        with open(caminho_resposta, "r", encoding="utf-8") as chaves:
            responder_chaves = json.load(chaves)

        return responder_chaves
    else:
        print(f"Erro: O arquivo '{caminho_resposta}' não encontrado.")

def training() -> None:
    print(""""
                    #####################################################################
                    #                                                                   #
                    #                  Treinamento da Assistente Virtual                #
                    #                           Melora V1.0                             #
                    #                                                                   #
                    #####################################################################
    """)
    
    print("\n                               Bem vindo ao sistema de treinamento da Melora!")
    print("         Aqui você pode treinar a Liora para reconhecer novas palavras chaves e associar respostas a elas.")
    print("Lembre-se que para ações (respostas numéricas) o arquivo 'organizador.py' deve ser configurado para reconhecer a ação.")

    while True:
        treinamento = int(input("\nO que deseja treinar? [1] Perguntas [2] Respostas [0] Sair: "))    
        
        if treinamento == 0:
            break

        visualizar = int(input("Você deseja visualizar os dados atuais? [1] Sim [2] Não: "))

        if treinamento == 1: # Treinar perguntas
            if visualizar == 1:
                print("\n"+str(get_keywords())+"\n")

            demanda = str(input("\nInforme qual a demanda da palavra chave (ex. para a demanda 'cumprimentar' a palavra chave pode ser 'olá'): "))
            print(f"\nPara as palavras chaves a resposta será '{demanda}'.")
            print(f"Lembre-se para novas demandas, o 'respostas_termos' deve ser treinado e para ações o arquivo organizador.py deve se configurado.")

            # Precisa abrir o arquivo .json no modo escrita e verificar se a palavra chave para demanda já existe
            # Se não existir, adicionar a nova palavra chave para demanda, se existir, adicionar a palavra chave na lista de palavras chaves da demanda
            with open(caminho_termo, "r+", encoding='utf-8') as arquivo:
                dados = json.load(arquivo)

                while True:
                    palavra = str(input("Informe a palavra chave (ou '0' para sair): "))
                    if palavra == '0':
                        break

                    if demanda in dados:
                        if palavra not in dados[demanda]:
                            dados[demanda].append(palavra)
                    else:
                        dados[demanda] = [palavra]

                    # Move o cursor para o início do arquivo para sobrescrever os dados
                    arquivo.seek(0)
                    json.dump(dados, arquivo, ensure_ascii=False, indent=4)
                    arquivo.truncate()  # Remove qualquer dado remanescente no arquivo após a nova escrita
                    
                    print(f"A palavra chave '{palavra}' será associada a demanda '{demanda}'.\n")

        elif treinamento == 2: # Treinar respostas
            if visualizar == 1:
                print("\n"+str(get_response_keywords()))

            demanda = str(input("\nInforme qual a demanda que deseja responder (ex. 'cumprimentar' ou '1' para ações): "))
            print(f"\nPara a demanda '{demanda}' a resposta pode ser uma frase (ex. 'Olá, como posso ajudar?') ou um dígito/int (ex. '1' para ações).")
            responder = str(input("Informe a resposta (ou '0' para sair): "))
            print(f"A resposta para a demanda '{demanda}' será '{responder}'.")

            # Precisa abrir o arquivo .json no modo escrita e verificar se a demanda já existe
            with open(caminho_resposta, "r+", encoding='utf-8') as arquivo:
                dados = json.load(arquivo)

                if responder == '0':
                    break

                # Tenta converter a resposta para int, se possível
                try:
                    resposta_convertida: str | int = int(responder)
                except ValueError:
                    resposta_convertida = responder

                dados[demanda] = resposta_convertida

                # Move o cursor para o início do arquivo para sobrescrever os dados
                arquivo.seek(0)
                json.dump(dados, arquivo, ensure_ascii=False, indent=4) # Sobrescreve os dados no arquivo
                arquivo.truncate()  # Remove qualquer dado remanescente no arquivo após a nova escrita
                
                print(f"A demanda '{demanda}' terá a resposta '{responder}'.")


if __name__ == '__main__':
    training()