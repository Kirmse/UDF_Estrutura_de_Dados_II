rede = {
    "Isaque": ["Liz", "Gabriel", "Jamilly"],
    "Liz": ["Isaque", "Gabriel"],
    "Gabriel": ["Isaque", "Liz", "Jamilly", "Ana"],
    "Jamilly": ["Isaque", "Gabriel", "Pedro", "Eduarda", "Ana"],
    "Pedro": ["Jamilly", "Vinicius"],
    "Eduarda": ["Jamilly", "Fernando"],
    "Vinicius": ["Pedro", "Fernando"],
    "Ana": ["Gabriel", "Jamilly"],
    "Fernando": ["Eduarda", "Vinicius", "Lucas"],
    "Lucas": ["Fernando"]
}

# Quantidade de usuarios
n = len(rede)

# Calcule o grau de cada usuario
for usuario, amigos in rede.items():
    print(usuario, "tem", len(amigos), "conexoes")

# A soma dos graus conta cada amizade duas vezes
soma_graus = sum(len(amigos) for amigos in rede.values())
arestas = soma_graus // 2

print("Total de usuarios:", n)
print("Total de amizades:", arestas)

# Densidade do grafo
densidade = (2 * arestas) / (n * (n - 1))
print(f"Densidade: {densidade:.2%}")