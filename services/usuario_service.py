import hashlib
import os
import mysql.connector
from database import conectar

class UsuarioService:

    @staticmethod
    def criar_usuario(nome, sobrenome, email, senha, is_admin=False):
        conexao = conectar()
        cursor = conexao.cursor()

        # Criar um salt aleatório
        salt = os.urandom(16).hex()

        senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()

        try:
            query = "INSERT INTO usuarios (nome, sobrenome, email, senha, admin) VALUES (%s,%s, %s, %s, %s)"
            valores = (nome, sobrenome, email, senha_hash, int(is_admin))
            cursor.execute(query, valores)
            conexao.commit()

            return {"status": "sucesso", "message": "Usuário criado com sucesso!"}
        except mysql.connector.IntegrityError:
            return {"status": "erro", "message": "E-mail já cadastrado!"}
        finally:
            cursor.close()
            conexao.close()

    @staticmethod
    def criar_admin_padrao():
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE admin = 1")
        admin_existe = cursor.fetchone()

        if not admin_existe:
            print("🛠 Criando usuário administrador...")

            nome = "Admin"
            sobrenome = "Sistema"
            email = "admin@example.com"
            senha = "admin123"


            UsuarioService.criar_usuario(nome, sobrenome, email, senha, is_admin=True)

            print("Usuário administrador criado com sucesso!")

        cursor.close()
        conexao.close()