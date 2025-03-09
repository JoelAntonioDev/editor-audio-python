from database import conectar
from datetime import datetime


class HistoricoService:
    @staticmethod
    def registrar_atividade(user_id, projeto_id, tipo_atividade, descricao):
        try:
            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO historico_atividades (user_id, projeto_id, tipo_atividade, descricao, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, projeto_id, tipo_atividade, descricao, datetime.now()))

            conn.commit()
            cursor.close()
            conn.close()

            return {"status": "sucesso", "message": "Atividade registrada com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}
