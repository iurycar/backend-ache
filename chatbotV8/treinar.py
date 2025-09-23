from pathlib import Path

diretorio = Path(__file__).parent
caminho_termo = diretorio / "dados" / "termos_chaves.txt"
caminho_resposta = diretorio / "dados" / "respostas.txt"

# Função para acessar os dados treinados para perguntas no aqui termos_chaves.txt
def termos_chaves() -> dict:
    # Verifica se o arquivo existe
    if caminho_termo.exists():
        palavras_chave = {}

        # Abre o arquino modo leitura e utiliza o sistema de codificação de caracteres "utf-8"
        with open(caminho_termo, "r", encoding="utf-8") as termos:
            linhas = termos.readlines() # Ler o arquivo por linhas

            # Passa por todas as linhas do arquivo
            for i in range(len(linhas)):
                palavra = linhas[i].replace("\n", "")
                termo = palavra.split("::") # Separa o dado no '::' (ex. 'olá :: cumprimentar' -> ['olá ', ' cumprimentar'])

                # Verifica se tem o termo e a demanda
                if len(termo) != 1:
                    chave = termo[0].strip() # Pega somente o termo e remove o espaço em branco
                    demanda = termo[1].strip() # Pega somente a demanda e remove o espaço em branco

                    palavras_chave[chave] = demanda

        return palavras_chave

    else:
        print(f"Erro: O arquivo '{caminho_termo}' não encontrado.")
    
def respostas_termos() -> dict:
    if caminho_resposta.exists():
        responder_chaves = {}

        with open(caminho_resposta, "r", encoding="utf-8") as chaves:
            linhas = chaves.readlines()
            
            for i in range(len(linhas)):
                palavra = linhas[i].replace("\n", "")
                termo = palavra.split("::")

                if len(termo) != 1:
                    chave = termo[0].strip()
                    resposta_str = termo[1].strip()

                    try:
                        resposta = int(resposta_str)
                    except:
                        resposta = resposta_str

                    responder_chaves[chave] = resposta

        return responder_chaves
    else:
        print(f"Erro: O arquivo '{caminho_resposta}' não encontrado.")

def treinar() -> None:
    print(""""
                    #####################################################################
                    #                                                                   #
                    #                  Treinamento da Assistente Virtual                #
                    #                           Melora V0.8                             #
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
                print("\n"+str(termos_chaves())+"\n")

            demanda = str(input("\nInforme qual a demanda da palavra chave (ex. para a demanda 'cumprimentar' a palavra chave pode ser 'olá'): "))
            print(f"\nPara as palavras chaves a resposta será '{demanda}'.")
            print(f"Lembre-se para novas demandas, o 'respostas_termos' deve ser treinado e para ações o arquivo organizador.py deve se configurado.")

            with open(caminho_termo, "a", encoding="utf-8") as saida:
                while True:
                    palavra = str(input("Informe a palavra chave (ou '0' para sair): "))

                    if palavra == '0':
                        break
                    
                    saida.write(f"{palavra} :: {demanda}\n")

        elif treinamento == 2:
            if visualizar == 1:
                print("\n"+str(respostas_termos()))

            demanda = str(input("\nInforme qual a demanda que deseja responder (ex. 'cumprimentar' ou '1' para ações): "))
            print(f"\nPara a demanda '{demanda}' a resposta pode ser uma frase (ex. 'Olá, como posso ajudar?') ou um dígito/int (ex. '1' para ações).")
            responder = str(input("Informe a resposta (ou '0' para sair): "))
            print(f"A resposta para a demanda '{demanda}' será '{responder}'.")

            with open(caminho_resposta, "a", encoding='utf-8') as saida:
                saida.write(f"{demanda} :: {responder}\n")


if __name__ == '__main__':
    treinar()