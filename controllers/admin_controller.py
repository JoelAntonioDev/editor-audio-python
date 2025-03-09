import json
from services.admin_service import AdminService

class AdminController:
    @staticmethod
    def listar_usuarios(environ):
        """
        GET /api/admin/usuarios
        Retorna a lista de usuários cadastrados.

        Headers:
            - Authorization: Bearer <token>

        Response:
            - 200 OK: {"status": "sucesso", "usuarios": [{...}, {...}]}
            - 401 Unauthorized: {"status": "erro", "message": "Acesso negado"}
        """
        headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
        token = headers[1] if len(headers) > 1 else None

        response_data = AdminService.listar_usuarios(token)
        return response_data

    @staticmethod
    def listar_historico(environ):
        """
        GET /api/admin/historico
        Retorna o histórico de atividades.

        Headers:
            - Authorization: Bearer <token>

        Response:
            - 200 OK: {"status": "sucesso", "historico": [{...}, {...}]}
            - 401 Unauthorized: {"status": "erro", "message": "Acesso negado"}
        """
        headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
        token = headers[1] if len(headers) > 1 else None

        response_data = AdminService.listar_historico(token)
        return response_data