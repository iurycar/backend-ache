import re

""" 
    -> O que é o Algoritmo Aho-Corasick?
        O algoritmo de Aho-Corasick permite a pesquisa rápida de padrões em um texto. O conjunto de padrões de texto
    também é chamado de dicionário. O algoritmo constroe uma trie, em que 'm' é o tamanho total da maior string contida
    e 'k' é o tamanho do alfabeto utilizado. Dessa forma, o algoritmo monta um automato de estados finitos baseado na trie
    que processa o texto em tempo linear.
        Para nosso caso, montamos uma trie com todas as perguntas treinadas no chatbot, sendo que cada nó de output (saída)
    referencia uma demanda do usuário. Portanto, o automato busca a partir do texto (mensagem) de entrada na trie uma 
    correspondência, caso encontre devolve a demanda associada aquele output.

    -> O que é uma Trie?
        Uma trie, ou árvore de prefixos, é uma estrutura de dados usada para recuperação eficiente de strings ou sequências.
    Cada nó na trie representa um caractere, e os caminhos da raiz até os nós (folhas) formam palavras ou sequências completas.

    -> O que é um Autômato Finito?
        Um automato finito determinístico, também chamado de máquina de estados finita determinística, é um modelo que aceita 
    ou rejeita cadeias de caracteres com base em um conjunto de estados e transições entre esses estados.
"""

K: int = 26  # Número de caracteres no alfabeto (a-z)

# Cria um objeto Nó
class Node:
    """ Classe que representa um Nó na trie do automato Aho-Corasick. """
    def __init__(self, parent=-1, pchar='$'):
        self.next: list[int|None] = [None] * K  # Filhos do Nó
        self.output: bool = False               # Se for 'True', diz que a palavra termina nesse Nó

        # Cria os links entre os Nó(s)
        self.parent: int = parent               # Determina qual é o pai desse Nó
        self.pchar: str = pchar                 # Determina qual Nó levou do pai até esse
        self.link: int = -1                     # Link de falha

        self.go: list[int|None] = [None] * K    # Armazena as transições entre o automato

        self.outputs: set[str] = set()          # Armazena as palavras (chaves para respostas) que terminam nesse Nó

# Um objeto para armazeenar todos os métodos e atributos da Trie
class Automaton:
    """ Classe que representa o automato Aho-Corasick. """
    def __init__(self):
        self.trie = [Node()] # A lista trie começa com o nó raiz (índice 0)

    def char_to_index(self, char: str) -> int:
        """ Converte um caractere ('a'-'z') para um índice (0-25) """
        return ord(char) - ord('a')

    def add_string(self, string: str, values: str | None) -> None:
        """ Adiciona uma string na trie """
        v: int = 0 # Começa pelo Nó raiz
        string = self.normalize(string) # Normaliza a string

        for char in string:
            ch: int = self.char_to_index(char)
            
            # Se a transição não existe cria um novo Nó
            if (self.trie[v].next[ch] is None):
                self.trie[v].next[ch] = len(self.trie)

                # Cria um novo Nó, guardando seu pai (v) e o caractere (char)
                new_node = Node(parent=v, pchar=char)

                self.trie.append(new_node)

            # Avança para o próximo Nó    
            v = self.trie[v].next[ch]
        
        # Marca o último Nó como um Nó output (flag output)
        self.trie[v].output = True
        
        # Adiciona a string na lista de outputs do Nó
        if values is not None:
            self.trie[v].outputs.add(values)
        else:
            self.trie[v].outputs.add(string)

    def get_link(self, v: int) -> int:
        """
        Calcula e memoriza o link de falha para o Nó. Está é uma função recursiva.
        """

        node = self.trie[v] # Pega o Nó atual

        # Se já foi calculado e memorizado, apenas retorna
        if node.link == -1:

            # Caso seja o Nó raiz (v == 0) ou os filhos da raiz (parent == 0)
            if v == 0 or node.parent == 0:
                node.link = 0
            else:
                # Trecho recursivo
                # Encontra o link de falha do pai (node.parent)
                parent_link = self.get_link(node.parent)
                # A partir do link do pai, tenta avançar com o mesmo caractere (node.pchar)
                node.link = self.go(parent_link, node.pchar)
        
        return node.link
    
    def go(self, v: int, char: str):
        """ Calcula e memoriza a transição do automato a partir do Nó v com o caractere char.
        Está é uma função para percorrer o automato."""
        ch: int = self.char_to_index(char)
        node = self.trie[v]

        if node.go[ch] is None:
            if node.next[ch] is not None:
                node.go[ch] = node.next[ch]
            else:
                if v == 0:
                    node.go[ch] = 0
                else:
                    node.go[ch] = self.go(self.get_link(v), char)

        return node.go[ch]

    def normalize(self, string: str) -> str:
        """ Normaliza a string para conter apenas caracteres minúsculos a-z """
        return re.sub(r'[^a-z]', '', string.lower())

    def node_for(self, string: str) -> int | None:
        """ Retorna o índice do Nó alcançado após processar a string.
        Retorna None se a string não puder ser alcançada na trie. """
        
        string = self.normalize(string)
        v: int = 0  # Começa pelo Nó raiz

        for char in string:
            index: int = self.char_to_index(char)
            prox: int | None = self.trie[v].next[index]

            if prox is None:
                return None  # A string não pode ser alcançada na trie
            
            v = prox

        return v

    def contains_word(self, string: str) -> bool:
        """ Verifica se a trie contém a palavra completa """
        node_index = self.node_for(string)

        if node_index is not None and self.trie[node_index].output:
            return True
        
        return False

    def find_values(self, text: str) -> set[str]:
        """ Encontra todas as palavras chaves que são substrings da string fornecida. """
        
        text = self.normalize(text)
        v: int = 0  # Começa pelo Nó raiz
        found: set[str] = set()

        for char in text:
            v = self.go(v, char) # Avança no automato com o caractere atual

            # Verifica todos os outputs possíveis a partir do Nó atual
            current: int = v
            while current != 0: # Enquanto não chegar na raiz
                node = self.trie[current]
                
                if node.output and node.outputs: # Se for um Nó output, adiciona as palavras encontradas
                    found.update(node.outputs)
                current = self.get_link(current)

        if self.trie[0].output and self.trie[0].outputs: # Verifica a raiz também
            found.update(self.trie[0].outputs)
        
        return found

    def show_trie(self):
        """ Exibe a estrutura completa da trie. """
        print("Trie completa:\n")
        for i, node in enumerate(self.trie):
            print(">>" * 40)
            print(f"Nó {i}:")
            print(f"  Parent: {node.parent}, PChar: '{node.pchar}', Output: {node.output}")
            print(f"  Next: {[idx if idx is not None else '-' for idx in node.next]}")
            print(f"  Link: {node.link}")
            print(f"  Go: {[idx if idx is not None else '-' for idx in node.go]}")
            print("<<" * 40 + "\n")

if __name__ == '__main__':
    trie = Automaton() # Cria o automato

    keywords = ["he", "she", "his", "hers"] # Palavras chaves para adicionar na trie
    for string in keywords:
        trie.add_string(string)
    
    for word in ["she", "her", "hers", "he", "his", "hi"]:
        print(f"{word}: {trie.contains_word(word)}")

    #link = trie.get_link(3) # Pega o link do Nó 3 (que representa a palavra 'she')
    #print(f"Link do Nó 3: {link}")
    #print(f"    Transição do Nó 3 com 'e': {trie.go(3, 's')}")
    #print(f"    Transição do Nó 3 com 'a': {trie.go(3, 'h')}")
    #print(f"    Transição do Nó 3 com 'a': {trie.go(3, 'e')}")
    #print(f"    O nó 3 foi alcançado por: {trie.trie[3].pchar}")

    trie.show_trie()