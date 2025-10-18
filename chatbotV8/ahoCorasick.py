# Teste do algoritmo de Aho-Corasick para múltiplas palavras chaves

K: int = 26  # Número de caracteres no alfabeto (a-z)

# Cria um objeto Nó
class Node:
    def __init__(self, parent=-1, pchar='$'):
        self.next: list[None] = [None] * K  # Filhos do Nó
        self.output: bool = False           # Se for 'True', diz que a palavra termina nesse Nó

        # Cria os links entre os Nó(s)
        self.parent: int = parent           # Determina qual é o pai desse Nó
        self.pchar: str = pchar             # Determina qual Nó levou do pai até esse
        self.link: int = -1                 # Link de falha

        self.go: list[int | None] = [None] * K    # Armazena as transições entre o automato

# Um objeto para armazeenar todos os métodos e atributos da Trie
class Automaton:
    def __init__(self):
        self.trie = [Node()] # A lista trie começa com o nó raiz (índice 0)

    def char_to_index(self, char: str) -> int:
        """ Converte um caractere ('a'-'z') para um índice (0-25) """
        return ord(char) - ord('a')

    def add_string(self, string: str) -> None:
        """ Adiciona uma string na trie """
        v: int = 0 # Começa pelo Nó raiz
        
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

    def get_link(self, v: int) -> int:
        """
        Calcula e memoriza o link de falha para o Nó.
        Está é uma função recursiva.
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
    
    #link = trie.get_link(3) # Pega o link do Nó 3 (que representa a palavra 'she')
    #print(f"Link do Nó 3: {link}")
    #print(f"    Transição do Nó 3 com 'e': {trie.go(3, 's')}")
    #print(f"    Transição do Nó 3 com 'a': {trie.go(3, 'h')}")
    #print(f"    Transição do Nó 3 com 'a': {trie.go(3, 'e')}")
    #print(f"    O nó 3 foi alcançado por: {trie.trie[3].pchar}")

    trie.show_trie()