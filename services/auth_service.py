"""
Serviço de Autenticação

Este módulo fornece funções para autenticação de usuários, incluindo login
e verificação de tokens.

Módulos:
    - base64: Para codificar e decodificar dados em Base64.
    - json: Para manipular dados JSON.
    - time: Para trabalhar com timestamps.
    - hashlib: Para calcular hashes criptográficos.
    - database: Para conectar ao banco de dados.

Classes:
    - AuthService: Contém métodos para login e verificação de tokens.
"""
import base64
import json
import time
import hashlib
from database import conectar

class AuthService:
    """
        Classe AuthService para autenticação de usuários.

        Métodos:
            - login(body): Realiza o login do usuário com base nos dados fornecidos.
            - verificar_token(token): Verifica a validade do token fornecido.
    """
    def login(self, body):
        """
        Realiza o login do usuário com base nos dados fornecidos.

        Args:
            body (str): Corpo da requisição contendo email e senha do usuário.

        Returns:
            dict: Resposta contendo status e mensagem do resultado do login.
        """
        try:
            data = json.loads(body)
            email = data.get('email')
            senha = data.get('password')

            if not email or not senha:
                return {'status': 'erro', 'message': 'E-mail e senha são obrigatórios'}

            # Conectar ao banco de dados
            conn = conectar()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, senha, admin FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            cursor.close()
            conn.close()

            if not usuario:
                return {'status': 'erro', 'message': 'Credenciais inválidas'}


            senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()

            # Verificar se o hash calculado corresponde ao hash armazenado
            if senha_hash == usuario['senha']:
                token_data = {
                    "email": email,
                    "exp": time.time() + 86400,  # Expirar em 1 dia
                    "is_admin": bool(usuario['admin'])  # Adicionando status de admin ao token
                }
                token_json = json.dumps(token_data)
                token_base64 = base64.b64encode(token_json.encode()).decode()

                return {
                    "status": "sucesso",
                    "message": "Login bem-sucedido",
                    "token": token_base64,
                    "email": email,
                    "user_id": usuario['id'],
                    "is_admin": bool(usuario['admin'])  # Retornando status de admin
                }
            else:
                return {'status': 'erro', 'message': 'Credenciais inválidas'}

        except Exception as e:
            return {'status': 'erro', 'message': str(e)}

    @staticmethod
    def verificar_token(token):
        """
        Verifica a validade do token fornecido.

        Args:
            token (str): Token de autenticação a ser verificado.

        Returns:
            dict: Resposta contendo status, user_id, email e is_admin, ou mensagem de erro.
        """
        try:
            if not token:
                return {"status": "erro", "message": "Token ausente"}

            token_json = base64.b64decode(token + "==").decode()
            token_data = json.loads(token_json)

            if time.time() > token_data["exp"]:
                return {"status": "erro", "message": "Token expirado"}

            conn = conectar()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (token_data["email"],))
            usuario = cursor.fetchone()
            cursor.close()
            conn.close()

            if not usuario:
                return {"status": "erro", "message": "Usuário não encontrado"}

            return {
                "status": "sucesso",
                "user_id": usuario["id"],
                "email": token_data["email"],
                "is_admin": token_data["is_admin"]
            }

        except (base64.binascii.Error, json.JSONDecodeError):
            return {"status": "erro", "message": "Token inválido"}
        except Exception as e:
            return {"status": "erro", "message": str(e)}
