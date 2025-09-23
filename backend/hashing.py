import bcrypt

""""
    Esse arquivo é responsável por fazer o hash e a verificação de senhas
"""

# Função para fazer o hash da senha
def hashPassword(password: str) -> str:
    # Converte a senha de string para bytes
    password_bytes = password.encode('utf-8')
    
    # Gera um salt e faz o hash da senha
    salt_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))

    # Converte o hash de bytes para string antes de armazenar
    password_string = salt_password.decode('utf-8')
    print(f"Hash gerado (string): {password_string}")

    return password_string

# Função para verificar a senha
def checkPassword(password: str, hash_armazenado: str | bytes) -> bool:
    # Converte a senha de string para bytes
    password_bytes = password.encode('utf-8')

    # Se o hash armazenado for uma string, converte para bytes
    if isinstance(hash_armazenado, str):
        hash_armazenado = hash_armazenado.encode('utf-8')
    
    # O bcrypt lida com a extração do salt e a verifica se a senha bate
    return bcrypt.checkpw(password_bytes, hash_armazenado)