import json
from services.usuario_service import UsuarioService

class UsuarioController:
    """
        Controlador responsável por operações relacionadas a usuários.
        """
    @staticmethod
    def criar_usuario(environ):
        """
                POST /api/usuarios
                Cria um novo usuário no sistema.

                Body:
                    - {
                        "nome": "João",
                        "sobrenome": "Silva",
                        "email": "joao@example.com",
                        "password": "senha123"
                    }

                Response:
                    - 201 Created: {"status": "sucesso", "message": "Usuário criado com sucesso", "user_id": "<id do usuário>"}
                    - 400 Bad Request: {"status": "erro", "message": "Todos os campos são obrigatórios"}
                    - 500 Internal Server Error: {"status": "erro", "message": "Erro interno do servidor"}
                """
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0) or 0)
            request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
            data = json.loads(request_body)

            nome = data.get("nome")
            sobrenome = data.get("sobrenome")
            email = data.get("email")
            senha = data.get("password")

            if not all([nome, sobrenome, email, senha]):
                return {"status": "erro", "message": "Todos os campos são obrigatórios"}

            usuario_id = UsuarioService.criar_usuario(nome, sobrenome, email, senha)

            return {"status": "sucesso", "message": "Usuário criado com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def obter_usuario(environ, usuario_id):
        """
        GET /api/usuarios/{usuario_id}
        Obtém os dados de um usuário específico.

        Headers:
            - Authorization: Bearer <token>

        Response:
            - 200 OK: {"status": "sucesso", "usuario": {...}}
            - 404 Not Found: {"status": "erro", "message": "Usuário não encontrado"}
            - 500 Internal Server Error: {"status": "erro", "message": "Erro interno do servidor"}
        """
        try:
            headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
            token = headers[1] if len(headers) > 1 else None

            if not token:
                return {"status": "erro", "message": "Token ausente"}

            usuario = UsuarioService.obter_usuario(usuario_id, token)

            if not usuario:
                return {"status": "erro", "message": "Usuário não encontrado"}

            return {"status": "sucesso", "usuario": usuario}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def atualizar_usuario(environ, usuario_id):
        """
        PUT /api/usuarios/{usuario_id}
        Atualiza as informações de um usuário existente.

        Headers:
            - Authorization: Bearer <token>

        Body:
            - {
                "nome": "Novo Nome",
                "sobrenome": "Novo Sobrenome",
                "email": "novoemail@example.com"
            }

        Response:
            - 200 OK: {"status": "sucesso", "message": "Usuário atualizado com sucesso"}
            - 400 Bad Request: {"status": "erro", "message": "Nenhum dado fornecido para atualização"}
            - 401 Unauthorized: {"status": "erro", "message": "Token inválido"}
            - 404 Not Found: {"status": "erro", "message": "Usuário não encontrado"}
            - 500 Internal Server Error: {"status": "erro", "message": "Erro interno do servidor"}
        """
        try:
            headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
            token = headers[1] if len(headers) > 1 else None

            if not token:
                return {"status": "erro", "message": "Token ausente"}

            request_body_size = int(environ.get('CONTENT_LENGTH', 0) or 0)
            request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
            data = json.loads(request_body)

            if not data:
                return {"status": "erro", "message": "Nenhum dado fornecido para atualização"}

            sucesso = UsuarioService.atualizar_usuario(usuario_id, data, token)

            if not sucesso:
                return {"status": "erro", "message": "Usuário não encontrado"}

            return {"status": "sucesso", "message": "Usuário atualizado com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def deletar_usuario(environ, usuario_id):
        """
        DELETE /api/usuarios/{usuario_id}
        Exclui um usuário do sistema.

        Headers:
            - Authorization: Bearer <token>

        Response:
            - 200 OK: {"status": "sucesso", "message": "Usuário deletado com sucesso"}
            - 401 Unauthorized: {"status": "erro", "message": "Token inválido"}
            - 404 Not Found: {"status": "erro", "message": "Usuário não encontrado"}
            - 500 Internal Server Error: {"status": "erro", "message": "Erro interno do servidor"}
        """
        try:
            headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
            token = headers[1] if len(headers) > 1 else None

            if not token:
                return {"status": "erro", "message": "Token ausente"}

            sucesso = UsuarioService.deletar_usuario(usuario_id, token)

            if not sucesso:
                return {"status": "erro", "message": "Usuário não encontrado"}

            return {"status": "sucesso", "message": "Usuário deletado com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}