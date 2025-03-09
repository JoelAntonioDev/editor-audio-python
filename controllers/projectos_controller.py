import json
import mimetypes
import os
from email.parser import BytesParser
from email.policy import default
from services.projectos_service import ProjectosService

class ProjectosController:
    @staticmethod
    def listar_projectos(environ):
        """
                GET /api/projectos
                Retorna a lista de projetos do usuário autenticado.

                Headers:
                    - Authorization: Bearer <token>

                Response:
                    - 200 OK: {"status": "sucesso", "projectos": [...]}
                    - 401 Unauthorized: {"status": "erro", "message": "Token inválido"}
                """
        # Pegar token do cabeçalho Authorization
        headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
        token = headers[1] if len(headers) > 1 else None

        # Obter lista de projetos do serviço
        response_data = ProjectosService.listar_projectos(token)

        return response_data

    @staticmethod
    def criar_projecto(environ):
        token = ProjectosController._get_token(environ)

        if environ.get("REQUEST_METHOD") != "POST":
            return {"status": "erro", "message": "Método inválido"}

        form_data, files, error = ProjectosController._parse_multipart_data(environ)
        if "error" in form_data:
            return {"status": "erro", "message": error}

        titulo = form_data.get("titulo")
        audio_file = files.get("audio")
        print(titulo)
        if not titulo or not audio_file:
            return {"status": "erro", "message": "Título e áudio são obrigatórios"}

        # Salvar o arquivo
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, audio_file["filename"])

        try:
            with open(file_path, "wb") as f:
                f.write(audio_file["file"])

            return ProjectosService.criar_projecto(token, titulo, audio_file)

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def obter_projecto(environ, project_id):
        token = ProjectosController._get_token(environ)
        return ProjectosService.obter_projecto(token, project_id)

    @staticmethod
    def retroceder_edicao(environ, project_id, file_name):
        token = ProjectosController._get_token(environ)

        if not token:
            return {"status": "erro", "message": "Token não fornecido"}

        return ProjectosService.retroceder_edicao(token, project_id, file_name)

    @staticmethod
    def upload_audio(environ):
        token = ProjectosController._get_token(environ)

        if environ.get("REQUEST_METHOD") != "POST":
            return {"status": "erro", "message": "Método inválido"}

        content_type = environ.get("CONTENT_TYPE", "")
        if "multipart/form-data" not in content_type:
            return {"status": "erro", "message": "Formato de dados inválido"}

        post_data, files, error = ProjectosController._parse_multipart_data(environ)

        if error:
            return {"status": "erro", "message": error["error"]}

        project_id = post_data.get("project_id", "")  # Agora, post_data é um dicionário
        audio_file = files.get("audio")

        if not project_id or not audio_file:
            return {"status": "erro", "message": "Projeto ou áudio não informado"}

        return ProjectosService.upload_audio(token, project_id, audio_file)

    @staticmethod
    def baixar_projecto(project_id, token):
        """
                GET /api/baixar-projecto/{project_id}
                Baixa o projeto como um arquivo ZIP.

                Headers:
                    - Authorization: Bearer <token>

                Response:
                    - 200 OK: Download do arquivo ZIP
                    - 400 Bad Request: {"status": "erro", "message": "Projeto não encontrado"}
                """
        return ProjectosService.baixar_projecto(token, project_id)

    @staticmethod
    def enviar_arquivo_zip(zip_file_path, project_id, start_response):
        """Envia o arquivo ZIP como resposta HTTP."""
        if os.path.exists(zip_file_path):
            mime_type, _ = mimetypes.guess_type(zip_file_path)
            mime_type = mime_type or "application/zip"

            with open(zip_file_path, "rb") as f:
                response_data = f.read()

            headers = [
                ('Content-Type', mime_type),
                ('Content-Disposition', f'attachment; filename="projeto_{project_id}.zip"'),
                ('Access-Control-Allow-Origin', '*'),  # Adicionar cabeçalho CORS aqui também
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
                ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            ]
            start_response('200 OK', headers)
            return [response_data]

        start_response('400 Bad Request', [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
            ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        ])
        return [json.dumps({"status": "erro", "message": "Arquivo ZIP não encontrado"}).encode("utf-8")]

    @staticmethod
    def _get_token(environ):
        """Obtém o token de autenticação do cabeçalho Authorization."""
        headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
        return headers[1] if len(headers) > 1 else None

    @staticmethod
    def _parse_multipart_data(environ):
        """Processa multipart/form-data."""
        content_type = environ.get("CONTENT_TYPE", "")
        if "multipart/form-data" not in content_type:
            return {}, {}, {"error": "Content-Type inválido"}

        content_length = int(environ.get("CONTENT_LENGTH", 0))
        body = environ["wsgi.input"].read(content_length)

        try:
            headers = f"Content-Type: {content_type}\r\n\r\n".encode() + body
            msg = BytesParser(policy=default).parsebytes(headers)

            post_data = {}
            files = {}

            for part in msg.iter_parts():
                name = part.get_param("name", header="content-disposition")
                filename = part.get_filename()

                print(f"🔹 Nome do campo: {name}")  # Verificando os campos recebidos
                print(f"🔹 Nome do arquivo: {filename}")  # Verificando se o arquivo está presente

                if filename:
                    files[name] = {
                        "filename": filename,
                        "file": part.get_payload(decode=True)
                    }
                else:
                    post_data[name] = part.get_payload(decode=True).decode()

            return post_data, files, None  # Retorna post_data, files e erro (None se não houver erro)
        except Exception as e:
            return {}, {}, {"error": f"Erro ao processar multipart: {str(e)}"}