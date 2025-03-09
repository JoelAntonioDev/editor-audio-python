import uuid
from database import conectar
from datetime import datetime, timedelta


class SessionService:
    @staticmethod
    @staticmethod
    def iniciar_sessao(user_id, token, ip_address):
        try:
            conn = conectar()
            cursor = conn.cursor()

            session_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=1)

            cursor.execute("""
                    INSERT INTO sessoes (user_id, session_id, token, ip_address, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, session_id, token, ip_address, datetime.now(), expires_at))

            conn.commit()
            cursor.close()
            conn.close()

            return {"status": "sucesso", "session_id": session_id}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def terminar_sessao(user_id):
        try:
            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
                    DELETE FROM sessoes WHERE user_id = %s
                """, (user_id,))

            conn.commit()
            cursor.close()
            conn.close()

            return {"status": "sucesso", "message": "Sessão terminada com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}