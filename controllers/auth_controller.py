from services.auth_service import AuthService
from services.login_service import LoginService
from services.session_service import SessionService
class AuthController:

    @staticmethod
    def login(environ):
        try:
            # Receber os dados da requisição
            length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(length).decode('utf-8') if length > 0 else ''

            auth_service = AuthService()
            response_data = auth_service.login(body)

            if response_data["status"] == "erro":
                return {"status": "erro", "message": response_data["message"]}

            user_id = response_data["user_id"]
            token = response_data["token"]
            # Obter endereço IP do usuário
            ip_address = environ.get('REMOTE_ADDR')

            LoginService.registrar_login(user_id, ip_address)
            session_response = SessionService.iniciar_sessao(user_id, token, ip_address)

            return response_data

        except Exception as e:
            return {'status': 'erro', 'message': str(e)}

    @staticmethod
    def logout(environ):
        try:
            headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
            token = headers[1] if len(headers) > 1 else None

            if not token:
                return {"status": "erro", "message": "Token ausente"}

            auth_response = AuthService.verificar_token(token)
            if auth_response["status"] == "erro":
                return {"status": "erro", "message": auth_response["message"]}

            user_id = auth_response["user_id"]

            response = SessionService.terminar_sessao(user_id)

            return response

        except Exception as e:
            return {'status': 'erro', 'message': str(e)}