# ===== O NÓ =====
# Molde para criar cada nó da árvore
class Node:
    # Construtor: roda sozinho quando você faz Node(valor)
    # "data" é o valor que você entrega ao criar o nó
    def __init__(self, data):
        self.data = data    # guarda o valor dentro do nó
        self.left = None    # filho da esquerda (começa vazio)
        self.right = None   # filho da direita (começa vazio)

    # Define o que aparece quando você faz print(nó)
    def __str__(self):
        return str(self.data)  # mostra só o valor, convertido em texto


# ===== A ÁRVORE =====
# Molde para criar a árvore, que guarda a raiz
class BinaryTree:
    # "data=None": o valor da raiz é opcional
    def __init__(self, data=None):
        if data:                # se veio um valor...
            node = Node(data)   # ...cria o nó da raiz
            self.root = node    # ...e o coloca como raiz da árvore
        else:                   # se não veio valor...
            self.root = None    # ...a árvore fica vazia

    def simetric_traversal(self, node=None):
        if node is None:
            node = self.root
        if node.left:
            print("(", end='')
            self.simetric_traversal(node.left)
        print(node, end='')
        if node.right:
            self.simetric_traversal(node.right)
            print(")", end='')
# ===== O TESTE =====
# Só roda se este arquivo for executado diretamente (não quando importado)
if __name__ == "__main__":
    # tree = BinaryTree(7)            # cria a árvore com raiz = 7
    # tree.root.left = Node(18)       # cria o nó 18 e o pendura à esquerda da raiz
    # tree.root.right = Node(13)      # cria o nó 13 e o pendura à direita da raiz
    #
    # print(tree.root)        # mostra a raiz -> 7
    # print(tree.root.right)  # mostra o filho direito -> 13
    # print(tree.root.left)   # mostra o filho esquerdo ->

    tree = BinaryTree()
    n1 = Node('a')
    n2 = Node('b')
    n3 = Node('c')
    n4 = Node('d')
    n5 = Node('e')
    n6 = Node('+')
    n7 = Node('-')
    n8 = Node('/')
    n9 = Node('*')

    n6.left = n1
    n6.right = n9
    n9.left = n2
    n9.right = n7
    n7.left = n8
    n7.right = n5
    n8.left = n3
    n8.right = n4

    tree.root = n6
    tree.simetric_traversal()

# (a+(b*((c/d)-e)))
