from pathlib import Path

diretorio = Path(__file__).parent
caminho_termo = diretorio / "dados" / "termos_chaves.txt"
caminho_resposta = diretorio / "dados" / "respostas.txt"

# Função para acessar os dados treinados para perguntas no aqui termos_chaves.txt
def termos_chaves():
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
    
def respostas_termos():
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

def treinar():
    while True:
        treinamento = int(input("Informe qual o treinamento - [1] Perguntas / [2] Respostas / [0] Encerrar: "))    
        
        if treinamento == 0:
            break

        visualizar = int(input("Deseja visualizar os dados armazenados? [1] Sim [2] Não: "))

        if treinamento == 1: # Treinar perguntas
            if visualizar == 1:
                print("\n"+str(termos_chaves())+"\n")

            demanda = str(input("Informe o tipo de demanda para a pergunta\n(ex. para a palavra 'olá' a demanda será 'cumprimentar'): "))
            print(f"\nPara as palavras chaves a resposta será '{demanda}'.")
            print(f"Lembre-se para novas demandas, o 'respostas_termos' deve ser treinado e para ações o arquivo organizador.py deve se configurado.")

            with open(caminho_termo, "a", encoding="utf-8") as saida:
                while True:
                    palavra = str(input(f"\nInforme a palavra chave para a demanda '{demanda}' (Digite '0' para encerrar): "))

                    if palavra == '0':
                        break
                    
                    saida.write(f"{palavra} :: {demanda}\n")

        elif treinamento == 2:
            if visualizar == 1:
                print("\n"+str(respostas_termos()))

            demanda = str(input("\nInforme qual a demanda da resposta \n(ex. resposta para a demanda 'cumprimentar' a resposta é 'Olá!',\npara as ações a resposta deve ser um dígito/int): "))
            responder = str(input("Informe qual a resposta para a demanda: "))

            with open(caminho_resposta, "a", encoding='utf-8') as saida:
                saida.write(f"{demanda} :: {responder}\n")


if __name__ == '__main__':
    treinar()