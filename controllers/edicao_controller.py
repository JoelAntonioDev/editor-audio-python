import os
import json
import re
from datetime import datetime

import database
import ffmpeg
from controllers.projectos_controller import ProjectosController
from database import conectar
from services.auth_service import AuthService
from services.edicao_service import EdicaoAudioService
from services.historico_service import HistoricoService
from services.projectos_service import ProjectosService

UPLOAD_DIR = "uploads"
BASE_URL = "http://localhost:8000/"
class EdicaoAudioController:
    @staticmethod
    def recortar_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)

            data = json.loads(request_body.decode("utf-8"))  # Garantir UTF-8

            project_id = data.get("project_id")
            file_name = data.get("file_name")
            inicio = int(data.get("inicio", 0))
            fim = int(data.get("fim", 0))

            if not project_id or not file_name:
                return {"status": "erro", "message": "project_id e file_name são obrigatórios."}

            return EdicaoAudioService.recortar_audio(project_id, file_name, inicio, fim)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def mesclar_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            data = json.loads(request_body)

            # Autenticação do usuário
            token = ProjectosController._get_token(environ)
            auth_response = AuthService.verificar_token(token)

            if auth_response["status"] == "erro":
                return {"status": "erro", "message": "Acesso negado"}, 401

            user_id = auth_response["user_id"]
            project_id = data["project_id"]
            file1_name = data["file1"]
            file2_name = data["file2"]

            return EdicaoAudioService.mesclar_audio(project_id, file1_name, file2_name, user_id)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}, 500


    @staticmethod
    def alongar_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            data = json.loads(request_body.decode("utf-8"))  # Garante que está em UTF-8

            project_id = data.get("project_id")
            file_name = data.get("file_name")
            start_time = float(data.get("start_time", 0))
            end_time = float(data.get("end_time", 0))

            return EdicaoAudioService.alongar_audio(project_id, file_name, start_time, end_time)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except UnicodeDecodeError:
            return {"status": "erro", "message": "Erro de codificação. Verifique se a requisição está correta."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def encurtar_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            data = json.loads(request_body.decode("utf-8"))

            project_id = data.get("project_id")
            file_name = data.get("file_name")
            start_time = float(data.get("start_time", 0))
            end_time = float(data.get("end_time", 0))

            return EdicaoAudioService.encurtar_audio(project_id, file_name, start_time, end_time)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except UnicodeDecodeError:
            return {"status": "erro", "message": "Erro de codificação. Verifique se a requisição está correta."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def excluir_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)

            print(f"🔹 Request recebido: {request_body[:150]}")  # Debugging

            data = json.loads(request_body.decode("utf-8"))  # Garante que está em UTF-8

            project_id = data.get("project_id")
            file_name = data.get("file_name")

            if not project_id or not file_name:
                return {"status": "erro", "message": "project_id e file_name são obrigatórios."}

            # Conectar ao banco de dados
            conn = conectar()
            cursor = conn.cursor()

            # Verificar se o arquivo pertence ao projeto
            cursor.execute("""
                    SELECT audio_files.id, audio_files.file_path FROM audio_files 
                    JOIN projectos_audio_files ON audio_files.id = projectos_audio_files.audio_id 
                    WHERE projectos_audio_files.project_id = %s AND audio_files.file_name = %s
                """, (project_id, file_name))

            result = cursor.fetchone()

            if not result:
                cursor.close()
                conn.close()
                return {"status": "erro", "message": "Arquivo não encontrado para este projeto."}

            audio_id, file_path = result

            # Remover "http://localhost:8000/" do file_path, deixando apenas "/uploads/..."
            file_path = re.sub(r'^https?://localhost:\d+/', '', file_path)

            # Garantir que file_path não tenha "uploads/" duplicado
            if not file_path.startswith(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, file_path.lstrip("/"))

            # Excluir o arquivo do sistema
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🔹 Arquivo {file_name} removido do sistema.")

            # Remover do banco de dados
            cursor.execute("DELETE FROM projectos_audio_files WHERE audio_id = %s", (audio_id,))
            cursor.execute("DELETE FROM audio_files WHERE id = %s", (audio_id,))
            conn.commit()

            cursor.close()
            conn.close()

            return {"status": "sucesso", "message": f"Arquivo {file_name} excluído com sucesso."}

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except UnicodeDecodeError:
            return {"status": "erro", "message": "Erro de codificação. Verifique se a requisição está correta."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def excluir_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            data = json.loads(request_body.decode("utf-8"))

            project_id = data.get("project_id")
            file_name = data.get("file_name")

            return EdicaoAudioService.excluir_audio(project_id, file_name)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except UnicodeDecodeError:
            return {"status": "erro", "message": "Erro de codificação. Verifique se a requisição está correta."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}