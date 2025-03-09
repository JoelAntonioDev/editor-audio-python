from datetime import datetime

from services.auth_service import AuthService
from database import conectar

class AdminService:
    @staticmethod
    def listar_usuarios(token):
        # Verifica se o token é válido e se o usuário é admin
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        if not auth_response["is_admin"]:
            return {"status": "erro", "message": "Apenas administradores podem acessar esta rota."}

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id, email, admin FROM usuarios")
            usuarios = cursor.fetchall()

            cursor.close()
            conn.close()

            return {"status": "sucesso", "usuarios": usuarios}

        except Exception as e:
            return {"status": "erro", "message": str(e)}


    @staticmethod
    def listar_historico(token):
        # Verifica se o token é válido e se o usuário é admin
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        if not auth_response["is_admin"]:
            return {"status": "erro", "message": "Apenas administradores podem acessar esta rota."}

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                       SELECT h.id, u.email AS usuario, h.tipo_atividade, h.descricao, h.timestamp
                       FROM historico_atividades h
                       JOIN usuarios u ON h.user_id = u.id
                       ORDER BY h.timestamp DESC
                   """)
            historico = cursor.fetchall()

            # Converte datetime para string
            for item in historico:
                if isinstance(item["timestamp"], datetime):
                    item["timestamp"] = item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            cursor.close()
            conn.close()

            return {"status": "sucesso", "historico": historico}

        except Exception as e:
            return {"status": "erro", "message": str(e)}