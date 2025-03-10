"""
Servidor WSGI para gerenciar rotas e processamento de requests HTTP.

Este servidor utiliza wsgiref.simple_server para rodar na porta 8000 e
processa diferentes endpoints para autenticação, gerenciamento de usuários
e projetos, manipulação de áudio, entre outros.

Módulos:
    - email.parser: Usado para analisar uploads multipart/form-data.
    - urllib.parse: Utilizado para analisar query strings.
    - wsgiref.simple_server: Fornece um servidor WSGI simples.
    - os: Fornece uma maneira de usar funcionalidades do sistema operacional.
    - json: Permite manipulação de dados JSON.
    - mimetypes: Para adivinhar tipos MIME de arquivos.
    - controllers.auth_controller: Gerencia autenticação de usuários.
    - controllers.usuario_controller: Gerencia criação e listagem de usuários.
    - services.auth_service: Fornece serviços de autenticação.
    - controllers.projectos_controller: Gerencia operações com projetos.

Funções:
    - parse_multipart(environ): Substitui cgi.FieldStorage para lidar com uploads multipart/form-data.
    - application(environ, start_response): Função principal WSGI que processa requests e chama os controladores apropriados.
"""

from email.parser import BytesParser
from email.policy import default
from urllib.parse import parse_qs
from urllib.parse import unquote
from wsgiref.simple_server import make_server
import os
import json
import mimetypes

from controllers.admin_controller import AdminController
from controllers.auth_controller import AuthController
from controllers.edicao_controller import EdicaoAudioController
from controllers.usuario_controller import UsuarioController
from database import criar_banco, criar_tabelas
from services.auth_service import AuthService
from controllers.projectos_controller import ProjectosController
from services.documentacao_service import DocumentacaoService
from services.usuario_service import UsuarioService

UPLOAD_DIR = "uploads"  # Pasta onde os arquivos serão armazenados
os.makedirs(UPLOAD_DIR, exist_ok=True)
criar_banco()  # Cria o banco de dados, se necessário
criar_tabelas()  # Cria as tabelas dentro do banco 'jaudio'
UsuarioService.criar_admin_padrao()

def parse_multipart(environ):
    content_type = environ.get('CONTENT_TYPE', '')

    if 'multipart/form-data' in content_type:
        length = int(environ.get('CONTENT_LENGTH', 0))
        body = environ['wsgi.input'].read(length)
        headers = {'Content-Type': content_type}
        parsed = BytesParser(policy=default).parsebytes(b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + body)
        return parsed
    else:
        return parse_qs(environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', 0))).decode())

def application(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    method = environ['REQUEST_METHOD']

    # Cabeçalhos CORS padrão
    cors_headers = [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization')  # Adicionando Authorization
    ]

    # Responder requisições OPTIONS
    if method == 'OPTIONS':
        start_response('200 OK', [('Content-Type', 'text/plain')] + cors_headers)
        return [b'']
    # Servindo arquivos estáticos da pasta "uploads"
    if path.startswith("uploads/"):
        decoded_path = unquote(path.replace("uploads/", ""))  # 🔹 Decodificar a URL
        file_path = os.path.join(UPLOAD_DIR, decoded_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"

            with open(file_path, "rb") as f:
                response_body = f.read()

            start_response('200 OK', [('Content-Type', mime_type)] + cors_headers)
            return [response_body]

        start_response('404 Not Found', [('Content-Type', 'application/json')] + cors_headers)
        return [json.dumps({"status": "erro", "message": "Arquivo não encontrado"}).encode("utf-8")]
    if path == 'api/admin/usuarios' and method == 'GET':
        response_body = AdminController.listar_usuarios(environ)
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response('200 OK', headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == 'api/admin/historico' and method == 'GET':
        response_body = AdminController.listar_historico(environ)
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response('200 OK', headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == 'api/admin/logins' and method == 'GET':
        response_body = AdminController.listar_logins(environ)
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response('200 OK', headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == 'api/auth/login' and method == 'POST':
        response_body = AuthController.login(environ)
        status_code = '200 OK' if response_body.get("status") == "sucesso" else '401 Unauthorized'
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == 'api/auth/logout' and method == 'POST':
        response_body = AuthController.logout(environ)
        status_code = '200 OK' if response_body.get("status") == "sucesso" else '400 Bad Request'
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == 'api/usuarios' and method == 'GET':
        headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
        token = headers[1] if len(headers) > 1 else None

        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            start_response('401 Unauthorized', cors_headers + [('Content-Type', 'application/json')])
            return [json.dumps(auth_response).encode("utf-8")]

        start_response('200 OK', cors_headers + [('Content-Type', 'application/json')])
        return [json.dumps({"status": "sucesso", "usuarios": ["Admin", "User1"]}).encode("utf-8")]

    if path == 'api/usuarios' and method == 'POST':
        response_body = UsuarioController.criar_usuario(environ)
        status_code = '201 CREATED' if response_body.get("status") == "sucesso" else '401 Unauthorized'
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == 'api/projectos' and method == 'GET':
        response_body = ProjectosController.listar_projectos(environ)

        # Definir status de resposta com base no retorno
        status_code = '200 OK' if response_body.get("status") == "sucesso" else '401 Unauthorized'

        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response(status_code, headers)

        return [json.dumps(response_body).encode("utf-8")]

    if path.startswith('api/undo-audio/') and method == 'GET':
        try:
            parts = path.split('/')
            if len(parts) < 4:  # Garante que temos /api/undo-audio/{project_id}/{file_name}
                raise ValueError("Parâmetros insuficientes")

            project_id = int(parts[2])  # Captura o ID do projeto
            file_name = "/".join(parts[3:])  # Captura o nome do arquivo (podendo ter '/')

            response_body = ProjectosController.retroceder_edicao(environ, project_id, file_name)
            status_code = '200 OK' if response_body.get("status") == "sucesso" else '400 Bad Request'
            headers = cors_headers + [('Content-Type', 'application/json')]
            start_response(status_code, headers)
            return [json.dumps(response_body).encode("utf-8")]

        except ValueError:
            start_response('400 Bad Request', cors_headers + [('Content-Type', 'application/json')])
            return [json.dumps({"status": "erro", "message": "ID do projeto inválido ou parâmetros ausentes"}).encode(
                "utf-8")]

    if path == 'api/projectos' and method == 'POST':
        response_body = ProjectosController.criar_projecto(environ)
        status_code = '201 Created' if response_body.get("status") == "sucesso" else '400 Bad Request'
        headers = cors_headers + [('Content-Type', 'application/json')]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path.startswith('api/projectos/') and method == 'GET':
        try:
            project_id = int(path.split('/')[-1])
            response_body = ProjectosController.obter_projecto(environ, project_id)
            status_code = '200 OK' if response_body.get("status") == "sucesso" else '404 Not Found'
            headers = cors_headers + [('Content-Type', 'application/json')]
            start_response(status_code, headers)
            return [json.dumps(response_body).encode("utf-8")]
        except ValueError:
            start_response('400 Bad Request', cors_headers + [('Content-Type', 'application/json')])
            return [json.dumps({"status": "erro", "message": "ID do projeto inválido"}).encode("utf-8")]

    if path.startswith('api/projectos/') and method == 'DELETE':
        try:
            project_id = int(path.split('/')[-1])
            response_body = ProjectosController.excluir_projeto(environ, project_id)
            status_code = '200 OK' if response_body.get("status") == "sucesso" else '400 Bad Request'
            headers = cors_headers + [('Content-Type', 'application/json')]
            start_response(status_code, headers)
            return [json.dumps(response_body).encode("utf-8")]
        except ValueError:
            start_response('400 Bad Request', cors_headers + [('Content-Type', 'application/json')])
            return [json.dumps({"status": "erro", "message": "ID do projeto inválido"}).encode("utf-8")]

    if path == "api/upload-audio" and method == "POST":
        response_body = ProjectosController.upload_audio(environ)
        status_code = "201 Created" if response_body.get("status") == "sucesso" else "400 Bad Request"
        headers = cors_headers + [("Content-Type", "application/json")]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path.startswith('api/baixar-projecto/') and method == 'GET':
        try:
            project_id = int(path.split('/')[-1])
            headers = environ.get('HTTP_AUTHORIZATION', '').split("Bearer ")
            token = headers[1] if len(headers) > 1 else None

            response = ProjectosController.baixar_projecto(project_id, token)

            if response["status"] == "sucesso":
                return ProjectosController.enviar_arquivo_zip(response["zip_file_path"], project_id, start_response)

            start_response('400 Bad Request', cors_headers + [('Content-Type', 'application/json')])
            return [json.dumps(response).encode("utf-8")]

        except ValueError:
            start_response('400 Bad Request', cors_headers + [('Content-Type', 'application/json')])
            return [json.dumps({"status": "erro", "message": "ID do projeto inválido"}).encode("utf-8")]

    if path == "api/editar/recortar" and method == "POST":
        response_body = EdicaoAudioController.recortar_audio(environ)
        status_code = "200 OK" if response_body.get("status") == "sucesso" else "400 Bad Request"
        headers = cors_headers + [("Content-Type", "application/json")]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == "api/editar/mesclar" and method == "POST":
        response_body = EdicaoAudioController.mesclar_audio(environ)
        if isinstance(response_body, tuple):
            response_body, status_code = response_body  # Separando dicionário e código de status
        else:
            status_code = "200 OK" if response_body.get("status") == "sucesso" else "400 Bad Request"
        headers = cors_headers + [("Content-Type", "application/json")]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == "api/editar/alongar" and method == "POST":
        response_body = EdicaoAudioController.alongar_audio(environ)
        status_code = "200 OK" if response_body.get("status") == "sucesso" else "400 Bad Request"
        headers = cors_headers + [("Content-Type", "application/json")]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == "api/editar/encurtar" and method == "POST":
        response_body = EdicaoAudioController.encurtar_audio(environ)
        status_code = "200 OK" if response_body.get("status") == "sucesso" else "400 Bad Request"
        headers = cors_headers + [("Content-Type", "application/json")]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    if path == "api/audio/excluir" and method == "DELETE":
        response_body = EdicaoAudioController.excluir_audio(environ)
        status_code = "200 OK" if response_body.get("status") == "sucesso" else "400 Bad Request"
        headers = cors_headers + [("Content-Type", "application/json")]
        start_response(status_code, headers)
        return [json.dumps(response_body).encode("utf-8")]

    #documentação da API
    if path == 'api/documentacao' and method == 'GET':
        documentacao = gerar_documentacao()
        start_response('200 OK', [('Content-Type', 'application/json')] + cors_headers)
        return [json.dumps(documentacao, indent=4).encode("utf-8")]

    if path == 'documentacao' and method == 'GET':
        documentacao = gerar_documentacao()
        html_content = DocumentacaoService.gerar_documentacao_html(documentacao)

        start_response('200 OK', [('Content-Type', 'text/html')] + cors_headers)
        return [html_content.encode("utf-8")]

    # Resposta para rota não encontrada
    start_response('404 Not Found', cors_headers + [('Content-Type', 'application/json')])
    return [json.dumps({"status": "erro", "message": "Rota não encontrada"}).encode("utf-8")]

def gerar_documentacao():
    """
    Gerando automaticamente a documentação da API lendo as docstrings dos controladores.
    """
    import inspect
    from controllers.projectos_controller import ProjectosController
    from controllers.auth_controller import AuthController
    from controllers.usuario_controller import UsuarioController

    documentacao = {}

    for controller in [ProjectosController, AuthController, UsuarioController]:
        for nome, func in inspect.getmembers(controller, predicate=inspect.isfunction):
            doc = inspect.getdoc(func)
            if doc:
                documentacao[f"{controller.__name__}.{nome}"] = doc

    return documentacao


if __name__ == '__main__':
    with make_server('', 8000, application) as server:
        print("Servidor rodando na porta 8000 com CORS habilitado...")
        server.serve_forever()
