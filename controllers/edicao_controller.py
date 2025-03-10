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
            print("chegou")
            token = ProjectosController._get_token(environ)
            print("token", token)
            auth_response = AuthService.verificar_token(token)

            user_id = auth_response["user_id"]
            print(user_id)
            project_id = data.get("project_id")
            file_name = data.get("file_name")
            inicio = int(data.get("inicio", 0))
            fim = int(data.get("fim", 0))

            if not project_id or not file_name:
                return {"status": "erro", "message": "project_id e file_name são obrigatórios."}

            return EdicaoAudioService.recortar_audio(project_id, file_name, inicio, fim, user_id)

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

            token = ProjectosController._get_token(environ)
            auth_response = AuthService.verificar_token(token)

            user_id = auth_response["user_id"]
            project_id = data.get("project_id")
            file_name = data.get("file_name")
            start_time = float(data.get("start_time", 0))
            end_time = float(data.get("end_time", 0))

            return EdicaoAudioService.alongar_audio(project_id, file_name, start_time, end_time,user_id)

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

            token = ProjectosController._get_token(environ)
            auth_response = AuthService.verificar_token(token)

            user_id = auth_response["user_id"]
            project_id = data.get("project_id")
            file_name = data.get("file_name")
            start_time = float(data.get("start_time", 0))
            end_time = float(data.get("end_time", 0))

            return EdicaoAudioService.encurtar_audio(project_id, file_name, start_time, end_time,user_id)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except UnicodeDecodeError:
            return {"status": "erro", "message": "Erro de codificação. Verifique se a requisição está correta."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def aplicar_efeito(environ):
        try:
            request_body_size = int(environ.get("CONTENT_LENGTH", 0))
            print("entrou1")

            request_body = environ["wsgi.input"].read(request_body_size)
            print("entrou2")
            data = json.loads(request_body)

            token = ProjectosController._get_token(environ)
            auth_response = AuthService.verificar_token(token)
            user_id = auth_response["user_id"]

            project_id = data.get("project_id")
            file_name = data.get("file_name")
            efeito = data.get("efeito")
            print(user_id,project_id,file_name,efeito)
            return EdicaoAudioService.aplicar_efeito(project_id, file_name, efeito, user_id)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def excluir_audio(environ):
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            print(f"🔹 Request recebido: {request_body[:150]}")

            data = json.loads(request_body.decode("utf-8"))  # Garante que está em UTF-8
            token = ProjectosController._get_token(environ)
            auth_response = AuthService.verificar_token(token)

            user_id = auth_response["user_id"]
            project_id = data.get("project_id")
            file_name = data.get("file_name")

            if not project_id or not file_name:
                return {"status": "erro", "message": "project_id e file_name são obrigatórios."}

            return EdicaoAudioService.excluir_audio(project_id, file_name,user_id)

        except json.JSONDecodeError:
            return {"status": "erro", "message": "Erro ao decodificar JSON. Verifique o formato da requisição."}
        except UnicodeDecodeError:
            return {"status": "erro", "message": "Erro de codificação. Verifique se a requisição está correta."}
        except Exception as e:
            return {"status": "erro", "message": str(e)}