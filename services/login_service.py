from database import conectar
from datetime import datetime


class LoginService:
    @staticmethod
    def registrar_login(user_id, ip_address):
        try:
            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO registros_login (user_id, ip_address, timestamp)
                VALUES (%s, %s, %s)
            """, (user_id, ip_address, datetime.now()))

            conn.commit()
            cursor.close()
            conn.close()

            return {"status": "sucesso", "message": "Login registrado com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}
