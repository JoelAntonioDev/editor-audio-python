import os, re

import unicodedata

import database
from database import conectar
from services.auth_service import AuthService
from datetime import datetime
from services.historico_service import HistoricoService
import zipfile
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ProjectosService:
    @staticmethod
    def listar_projectos(token):
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            # Buscar todos os projetos do usuário e seus arquivos de áudio
            cursor.execute("""
                SELECT p.id, p.project_name, p.created_at, af.file_name, af.file_path
                FROM projectos p
                LEFT JOIN projectos_audio_files paf ON p.id = paf.project_id
                LEFT JOIN audio_files af ON paf.audio_id = af.id
                WHERE p.user_id = %s
            """, (user_id,))

            projetos_completos = cursor.fetchall()

            # Usar um dicionário para agrupar arquivos por projeto
            projectos_dict = {}
            for projeto in projetos_completos:
                project_id = projeto["id"]

                if project_id not in projectos_dict:
                    projectos_dict[project_id] = {
                        "id": projeto["id"],
                        "project_name": projeto["project_name"].strip(),
                        "created_at": projeto["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(
                            projeto["created_at"], datetime) else projeto["created_at"],
                        "arquivos": []  # Lista para armazenar os arquivos do projeto
                    }

                if projeto["file_name"] and projeto["file_path"]:
                    projectos_dict[project_id]["arquivos"].append({
                        "file_name": projeto["file_name"],
                        "file_path": projeto["file_path"],
                        "audio_url": f"http://localhost:8000/uploads/{os.path.basename(projeto['file_path'])}"
                    })

            # Converter dicionário para lista
            projectos = list(projectos_dict.values())

            cursor.close()
            conn.close()

            # Registrar atividade no histórico
            HistoricoService.registrar_atividade(user_id, None, "listagem", "Listagem de projetos")

            return {"status": "sucesso", "projectos": projectos}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def criar_projecto(token, titulo, audio_file):
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]
        #print(audio_file)
        file_name = audio_file.get("filename", "audio_default.mp3")
        normalized_filename = ProjectosService.normalizar_nome(file_name)
        file_path = os.path.join(UPLOAD_DIR, normalized_filename)
        print(normalized_filename)
        try:
            # Salvar o arquivo no servidor
            with open(file_path, "wb") as f:
                f.write(audio_file["file"])

            conn = conectar()
            cursor = conn.cursor()
            print("chegou")
            # 1️⃣ Inserir o arquivo de áudio na tabela audio_files
            cursor.execute(
                "INSERT INTO audio_files (file_name, file_path, duration) VALUES (%s, %s, %s)",
                (normalized_filename, file_path, 0)  # ⚠ Defina a duração real depois
            )
            audio_id = cursor.lastrowid  # Obtém o ID do áudio inserido

            # 2️⃣ Criar o projeto na tabela projectos
            cursor.execute(
                "INSERT INTO projectos (user_id, project_name) VALUES (%s, %s)",
                (user_id, titulo)
            )
            project_id = cursor.lastrowid  # Obtém o ID do projeto inserido

            # 3️⃣ Associar o projeto ao arquivo de áudio na tabela projectos_audio_files
            cursor.execute(
                "INSERT INTO projectos_audio_files (project_id, audio_id) VALUES (%s, %s)",
                (project_id, audio_id)
            )

            conn.commit()
            cursor.close()
            conn.close()

            # Registrar atividade no histórico
            HistoricoService.registrar_atividade(user_id, project_id, "criação", "Criou projeto")
            return {"status": "sucesso", "message": "Projeto criado com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def obter_projecto(token, project_id):
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            # 🔥 Buscar todos os áudios do projeto
            cursor.execute("""
                SELECT 
                    p.id AS project_id, 
                    p.project_name, 
                    p.created_at, 
                    af.id AS audio_id,
                    af.file_name, 
                    af.file_path,
                    af.created_at
                FROM projectos p
                LEFT JOIN projectos_audio_files paf ON p.id = paf.project_id
                LEFT JOIN audio_files af ON paf.audio_id = af.id
                WHERE p.id = %s AND p.user_id = %s
            """, (project_id, user_id))

            arquivos = list(cursor.fetchall())

            # 🔹 Se não houver áudios, retornar mensagem apropriada
            if not arquivos or all(a["file_name"] is None for a in arquivos):
                return {"status": "sucesso", "message": "Projeto encontrado, mas sem áudios", "arquivos": [], "project_name":arquivos[0]["project_name"].strip()}

            # 🔥 Criar um dicionário para armazenar apenas os arquivos mais recentes
            arquivos_filtrados = {}

            for arquivo in arquivos:
                # 🔹 Ignorar registros sem file_name (evita erro NoneType)
                if not arquivo["file_name"]:
                    continue

                if isinstance(arquivo["created_at"], datetime):
                    arquivo["created_at"] = arquivo["created_at"].strftime("%Y-%m-%d %H:%M:%S")

                # 🔹 Remover timestamp do nome do arquivo
                nome_base = re.sub(r"^\d+_", "", arquivo["file_name"])

                # 🔹 Verificar se já temos uma versão desse arquivo e comparar timestamps
                if nome_base not in arquivos_filtrados or arquivos_filtrados[nome_base]["created_at"] < arquivo[
                    "created_at"]:
                    arquivo["audio_url"] = f"http://localhost:8000/uploads/{os.path.basename(arquivo['file_path'])}"
                    arquivos_filtrados[nome_base] = arquivo

            cursor.close()
            conn.close()

            projecto = {
                "id": arquivos[0]["project_id"],
                "project_name": arquivos[0]["project_name"].strip(),
                "created_at": arquivos[0]["created_at"],
                "arquivos": list(arquivos_filtrados.values())  # 🔥 Apenas os mais recentes!
            }

            HistoricoService.registrar_atividade(user_id, project_id, "obter", "Requisitou projeto")

            return {"status": "sucesso", "projecto": projecto}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def excluir_projeto(token, project_id):
        """Exclui um projeto e seus áudios associados"""
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            # 🔹 Verificar se o projeto pertence ao usuário
            cursor.execute("SELECT id FROM projectos WHERE id = %s AND user_id = %s", (project_id, user_id))
            projeto = cursor.fetchone()

            if not projeto:
                return {"status": "erro", "message": "Projeto não encontrado ou não pertence ao usuário"}

            # 🔥 Buscar IDs e caminhos dos áudios associados
            cursor.execute("""
                SELECT af.id, af.file_path FROM audio_files af
                JOIN projectos_audio_files paf ON af.id = paf.audio_id
                WHERE paf.project_id = %s
            """, (project_id,))

            arquivos = cursor.fetchall()

            # 🔥 Remover os arquivos do sistema
            for arquivo in arquivos:
                file_path = arquivo["file_path"]
                if os.path.exists(file_path):
                    os.remove(file_path)

            # 🔥 Obter IDs dos arquivos de áudio para exclusão
            audio_ids = [arquivo["id"] for arquivo in arquivos]

            # 🔥 Excluir registros de relacionamento antes dos arquivos de áudio
            cursor.execute("DELETE FROM projectos_audio_files WHERE project_id = %s", (project_id,))

            # 🔥 Excluir os arquivos de áudio apenas se existirem
            if audio_ids:
                cursor.execute("DELETE FROM audio_files WHERE id IN (%s)" % ",".join(map(str, audio_ids)))

            # 🔥 Excluir o projeto
            cursor.execute("DELETE FROM projectos WHERE id = %s", (project_id,))

            conn.commit()
            cursor.close()
            conn.close()

            HistoricoService.registrar_atividade(user_id, project_id, "delete", "Projeto excluído")

            return {"status": "sucesso", "message": "Projeto excluído com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def normalizar_nome(nome):
        nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
        nome = nome.replace(" ", "_")  # Substituir espaços por _
        return nome

    #Adicionar audio ao projecto
    @staticmethod
    def upload_audio(token, project_id, audio_file):
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        # 🔹 Normalizar o nome do arquivo antes de salvar
        normalized_filename = ProjectosService.normalizar_nome(audio_file['filename'])
        file_path = os.path.join(UPLOAD_DIR, normalized_filename)

        try:
            conn = conectar()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM audio_files WHERE file_name = %s AND file_path = %s",
                (normalized_filename, file_path)
            )
            file_bd = cursor.fetchone()

            if file_bd:
                cursor.close()
                conn.close()
                return {"status": "insucesso", "message": "Áudio já existe, tente com outro nome"}

            # 🔹 Salvar o arquivo no servidor com o nome normalizado
            with open(file_path, "wb") as f:
                f.write(audio_file['file'])

            # Inserir o áudio na tabela
            cursor.execute(
                "INSERT INTO audio_files (file_name, file_path, duration) VALUES (%s, %s, %s)",
                (normalized_filename, file_path, 0)
            )
            audio_id = cursor.lastrowid

            # Associar áudio ao projeto
            cursor.execute(
                "INSERT INTO projectos_audio_files (project_id, audio_id) VALUES (%s, %s)",
                (project_id, audio_id)
            )

            conn.commit()
            cursor.close()
            conn.close()

            # Registrar atividade no histórico
            HistoricoService.registrar_atividade(user_id, project_id, "carregamento", "Carregou áudio novo")
            return {"status": "sucesso", "message": "Áudio salvo com sucesso", "file_path": file_path}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def retroceder_edicao(token, project_id, file_name):
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True, buffered=True)

            # 🔹 1️⃣ Buscar o arquivo específico
            cursor.execute("""
                SELECT af.id, af.file_name, af.file_path
                FROM projectos_audio_files paf
                JOIN audio_files af ON paf.audio_id = af.id
                WHERE paf.project_id = %s AND af.file_name = %s
            """, (project_id, file_name))

            arquivo = cursor.fetchone()

            if not arquivo:
                cursor.close()
                conn.close()
                return {"status": "erro", "message": "Arquivo não encontrado para este projeto"}

            audio_id = arquivo["id"]
            caminho_arquivo = arquivo["file_path"]

            # 🔎 2️⃣ Verificar se o arquivo tem timestamp no início (para evitar deletar o original)
            if not re.search(r"^\d{14}_", os.path.basename(caminho_arquivo)):
                cursor.close()
                conn.close()
                return {"status": "erro", "message": "Já não pode retroceder."}

            # 🔥 3️⃣ Apagar o arquivo do sistema
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)

            # 🔥 4️⃣ Remover o registro do áudio do banco de dados
            cursor.execute("DELETE FROM projectos_audio_files WHERE audio_id = %s", (audio_id,))
            conn.commit()

            cursor.execute("DELETE FROM audio_files WHERE id = %s", (audio_id,))
            conn.commit()

            # 🔹 5️⃣ Fechar e reabrir cursor antes da nova consulta
            cursor.close()
            cursor = conn.cursor(dictionary=True, buffered=True)

            cursor.execute("""
                SELECT af.file_name, af.file_path
                FROM projectos_audio_files paf
                JOIN audio_files af ON paf.audio_id = af.id
                WHERE paf.project_id = %s
                ORDER BY af.created_at DESC
            """, (project_id,))

            novo_arquivo = cursor.fetchone()

            cursor.close()
            conn.close()

            # Registrar atividade no histórico
            HistoricoService.registrar_atividade(user_id, project_id, "retroceder", "Retrocedeu edição")

            if novo_arquivo:
                return {
                    "status": "sucesso",
                    "message": "Retrocedido com sucesso",
                    "novo_audio_url": f"http://localhost:8000/uploads/{os.path.basename(novo_arquivo['file_path'])}"
                }
            else:
                return {
                    "status": "sucesso",
                    "message": "Retrocedido, mas não há mais áudios para este projeto"
                }

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def baixar_projecto(token, project_id):
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT af.file_name, af.file_path
                FROM projectos p
                LEFT JOIN projectos_audio_files paf ON p.id = paf.project_id
                LEFT JOIN audio_files af ON paf.audio_id = af.id
                WHERE p.id = %s AND p.user_id = %s
            """, (project_id, user_id))

            arquivos = cursor.fetchall()

            if not arquivos:
                return {"status": "erro", "message": "Projeto não encontrado ou sem arquivos"}

            # Criar diretório para ZIPs (se não existir)
            zip_dir = "zips"
            os.makedirs(zip_dir, exist_ok=True)

            # Caminho do ZIP
            zip_file_path = os.path.join(zip_dir, f"projeto_{project_id}.zip")

            # Criar o ZIP
            with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for arquivo in arquivos:
                    file_name = os.path.basename(arquivo["file_path"])
                    zip_subdir = "audios_originais/" if not re.match(r"^\d{14}_", file_name) else ""
                    zipf.write(arquivo["file_path"], os.path.join(zip_subdir, file_name))

            cursor.close()
            conn.close()

            return {"status": "sucesso", "message": "Download pronto", "zip_file_path": zip_file_path}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def apagar_projecto(token, project_id):
        """
        DELETE /api/projectos/{project_id}
        Exclui um projeto e seus arquivos associados.

        Headers:
            - Authorization: Bearer <token>

        Response:
            - 200 OK: {"status": "sucesso", "message": "Projeto apagado com sucesso"}
            - 401 Unauthorized: {"status": "erro", "message": "Token inválido"}
            - 403 Forbidden: {"status": "erro", "message": "Acesso negado"}
            - 404 Not Found: {"status": "erro", "message": "Projeto não encontrado"}
            - 500 Internal Server Error: {"status": "erro", "message": "Erro interno do servidor"}
        """
        auth_response = AuthService.verificar_token(token)
        if auth_response["status"] == "erro":
            return {"status": "erro", "message": "Acesso negado"}

        user_id = auth_response["user_id"]

        try:
            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            # Verificar se o projeto pertence ao usuário e obter os arquivos relacionados
            cursor.execute("""
                    SELECT af.id AS audio_id, af.file_path
                    FROM projectos p
                    LEFT JOIN projectos_audio_files paf ON p.id = paf.project_id
                    LEFT JOIN audio_files af ON paf.audio_id = af.id
                    WHERE p.id = %s AND p.user_id = %s
                """, (project_id, user_id))

            arquivos = cursor.fetchall()

            if not arquivos:
                return {"status": "erro", "message": "Projeto não encontrado ou não pertence ao usuário"}

            # Apagar arquivos do sistema de arquivos
            for arquivo in arquivos:
                file_path = arquivo["file_path"]
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)

            # Excluir registros do banco de dados
            cursor.execute("DELETE FROM projectos_audio_files WHERE project_id = %s", (project_id,))
            cursor.execute("DELETE FROM audio_files WHERE id IN (%s)" % ",".join(str(a["audio_id"]) for a in arquivos))
            cursor.execute("DELETE FROM projectos WHERE id = %s", (project_id,))

            conn.commit()
            cursor.close()
            conn.close()

            # Registrar atividade no histórico
            HistoricoService.registrar_atividade(user_id, project_id, "deleção", "Projeto apagado")

            return {"status": "sucesso", "message": "Projeto apagado com sucesso"}

        except Exception as e:
            return {"status": "erro", "message": str(e)}

    @staticmethod
    def verificar_audio_no_projeto(project_id, file_name, user_id):
        """
        Verifica se um arquivo de áudio pertence ao projeto do usuário autenticado.

        :param project_id: ID do projeto
        :param file_name: Nome do arquivo de áudio
        :param user_id: ID do usuário autenticado
        :return: "projeto_invalido" se o projeto não pertencer ao usuário,
                 "audio_invalido" se o áudio não estiver no projeto,
                 "valido" se tudo estiver correto.
        """
        try:
            conn = conectar()
            cursor = conn.cursor()

            # Verifica se o usuário tem acesso ao projeto
            cursor.execute(
                """
                SELECT COUNT(*) FROM projectos 
                WHERE id = %s AND user_id = %s
                """,
                (project_id, user_id)
            )
            projeto_existe = cursor.fetchone()[0] > 0

            if not projeto_existe:
                return "projeto_invalido"  # O projeto não pertence ao usuário

            # Verifica se o arquivo está associado ao projeto
            cursor.execute(
                """
                SELECT COUNT(*) FROM projectos_audio_files paf
                JOIN audio_files af ON paf.audio_id = af.id
                WHERE paf.project_id = %s AND af.file_name = %s
                """,
                (project_id, file_name)
            )
            audio_existe = cursor.fetchone()[0] > 0

            cursor.close()
            conn.close()

            if not audio_existe:
                return "audio_invalido"  # O áudio não pertence ao projeto

            return "valido"  # Tudo certo

        except Exception as e:
            print(f"Erro ao verificar áudio no projeto: {e}")
            return "erro"

    @staticmethod
    def remover_audio_do_projeto(project_id, file_name):
        try:
            conn = database.conectar()
            cursor = conn.cursor(buffered=True)  # 🔹 Adicionamos `buffered=True`

            print(file_name)

            # 🔹 Fechar cursor antes de executar uma nova consulta (se necessário)
            cursor.close()
            cursor = conn.cursor(buffered=True)

            # Buscar o ID do áudio antes de remover
            cursor.execute("SELECT id FROM audio_files WHERE file_name = %s", (file_name,))
            audio_id_rows = cursor.fetchall()  # 🔹 Pegamos todos os resultados

            if not audio_id_rows:
                print(f"Erro: áudio '{file_name}' não encontrado no banco de dados.")
                cursor.close()
                conn.close()
                return

            audio_id = audio_id_rows[0][0]  # Pegamos o primeiro ID encontrado

            # 🔹 Limpar possíveis resultados pendentes
            while cursor.nextset():
                pass

            # Remover da tabela `projectos_audio_files`
            cursor.execute("DELETE FROM projectos_audio_files WHERE project_id = %s AND audio_id = %s",
                           (project_id, audio_id))

            conn.commit()  # Confirmar remoção antes da próxima consulta

            # Remover da tabela `audio_files`
            cursor.execute("DELETE FROM audio_files WHERE id = %s", (audio_id,))

            conn.commit()  # Confirmar remoção final

            print(f"Áudio '{file_name}' removido do banco de dados com sucesso.")

        except Exception as e:
            print(f"Erro ao remover áudio do banco de dados: {e}")
        finally:
            cursor.close()
            conn.close()
