import os
import re

import database
import ffmpeg
from datetime import datetime
from database import conectar
from services.historico_service import HistoricoService
from services.projectos_service import ProjectosService

UPLOAD_DIR = "uploads"
BASE_URL = "http://localhost:8000/"

class EdicaoAudioService:
    @staticmethod
    def recortar_audio(project_id, file_name, inicio, fim, user_id):
        """Realiza o recorte do áudio e salva no banco de dados"""

        # Conectar ao banco para verificar se o arquivo existe no projeto
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_path FROM audio_files 
            JOIN projectos_audio_files ON audio_files.id = projectos_audio_files.audio_id 
            WHERE projectos_audio_files.project_id = %s AND audio_files.file_name = %s
        """, (project_id, file_name))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return {"status": "erro", "message": "Arquivo não encontrado para este projeto."}

        file_path = result[0]

        # Remover URL e ajustar caminho
        file_path = re.sub(r'^https?://localhost:\d+/', '', file_path)
        if not file_path.startswith(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file_path.lstrip("/"))

        # Verificar se o arquivo existe no sistema
        if not os.path.exists(file_path):
            return {"status": "erro", "message": "Arquivo de áudio não encontrado."}

        # Gerar nome do novo arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_base, file_ext = os.path.splitext(file_name)
        file_base = re.sub(r'^\d{14}_', '', file_base)  # Remover timestamp antigo se houver
        novo_arquivo = f"{timestamp}_{file_base}{file_ext}"
        novo_path = os.path.join(UPLOAD_DIR, novo_arquivo)

        # Verificar duração e recortar
        duracao = fim - inicio
        ffmpeg.input(file_path, ss=inicio, t=duracao).output(novo_path, format="mp3").run(overwrite_output=True)

        # Salvar no banco de dados
        from controllers.edicao_controller import EdicaoAudioController
        novo_audio_id = EdicaoAudioService.salvar_audio_no_banco(novo_arquivo, novo_path, duracao)

        # Associar ao projeto
        EdicaoAudioService.associar_audio_ao_projeto(project_id, novo_audio_id)
        HistoricoService.registrar_atividade(user_id, project_id, "edição", f"Recortou {file_name} com start_time {inicio} e end_time {fim}")
        return {"status": "sucesso", "file_name": novo_arquivo, "file_path": novo_path}

    @staticmethod
    def mesclar_audio(project_id, file1_name, file2_name, user_id):
        """Realiza a mesclagem de dois áudios pertencentes a um projeto"""

        # Verificar se os áudios pertencem ao projeto do usuário
        verificar1 = ProjectosService.verificar_audio_no_projeto(project_id, file1_name, user_id)
        verificar2 = ProjectosService.verificar_audio_no_projeto(project_id, file2_name, user_id)

        if verificar1 in ["projeto_invalido", "audio_invalido"]:
            return {"status": "erro", "message": f"O arquivo {file1_name} não pertence ao projeto {project_id}"}, 400
        if verificar2 in ["projeto_invalido", "audio_invalido"]:
            return {"status": "erro", "message": f"O arquivo {file2_name} não pertence ao projeto {project_id}"}, 400

        # Caminhos dos arquivos
        file1_path = os.path.join(UPLOAD_DIR, file1_name)
        file2_path = os.path.join(UPLOAD_DIR, file2_name)

        # Remover timestamp antigo, se houver
        def remover_timestamp(nome_arquivo):
            return re.sub(r'^\d{14}_', '', nome_arquivo)

        file1_name_clean = remover_timestamp(file1_name)
        file2_name_clean = remover_timestamp(file2_name)

        # Gerar novo nome com timestamp atualizado
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        novo_arquivo = f"{timestamp}_{file1_name_clean}_e_{file2_name_clean}.mp3"
        novo_path = os.path.join(UPLOAD_DIR, novo_arquivo).replace("\\", "/")

        # Verificar se o arquivo já existe para evitar duplicação
        file_url = f"{BASE_URL}/uploads/{novo_arquivo}"
        if os.path.exists(novo_path):
            return {"status": "sucesso", "file_name": novo_arquivo, "file_path": file_url}

        # Comando FFmpeg para mesclar os áudios
        (
            ffmpeg
            .filter([ffmpeg.input(file1_path), ffmpeg.input(file2_path)], 'amix', inputs=2, duration='longest')
            .output(novo_path, format="mp3")
            .run(overwrite_output=True)
        )

        # Obter duração do novo áudio
        from controllers.edicao_controller import EdicaoAudioController
        duration = EdicaoAudioService.obter_duracao_audio(novo_path)

        # Salvar no banco de dados
        audio_id = EdicaoAudioService.salvar_audio_no_banco(novo_arquivo, novo_path, duration)

        # Associar ao projeto
        EdicaoAudioService.associar_audio_ao_projeto(project_id, audio_id)
        HistoricoService.registrar_atividade(user_id, project_id, "edição", f"Mesclou {file1_name} com {file2_name}")
        return {"status": "sucesso", "file_name": novo_arquivo, "file_path": file_url}

    @staticmethod
    def alongar_audio(project_id, file_name, start_time, end_time,user_id):
        """Duplica um trecho do áudio entre `start_time` e `end_time`, alongando a duração total"""

        if not project_id or not file_name or start_time < 0 or end_time <= start_time:
            return {"status": "erro", "message": "Parâmetros inválidos."}

        # Verificar se o arquivo pertence ao projeto
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path FROM audio_files 
            JOIN projectos_audio_files ON audio_files.id = projectos_audio_files.audio_id 
            WHERE projectos_audio_files.project_id = %s AND audio_files.file_name = %s
        """, (project_id, file_name))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return {"status": "erro", "message": "Arquivo não encontrado para este projeto."}

        file_path = result[0]

        # Ajustar caminho do arquivo
        file_path = re.sub(r'^https?://localhost:\d+/', '', file_path)
        if not file_path.startswith(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file_path.lstrip("/"))

        if not os.path.exists(file_path):
            return {"status": "erro", "message": "Arquivo de áudio não encontrado."}

        # Criar nome do novo arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_base, file_ext = os.path.splitext(file_name)
        file_base = re.sub(r'^\d{14}_', '', file_base)  # Remover timestamp antigo
        novo_arquivo = f"{timestamp}_{file_base}{file_ext}"
        novo_path = os.path.join(UPLOAD_DIR, novo_arquivo)

        # Criar trecho extraído
        trecho_path = os.path.join(UPLOAD_DIR, f"trecho_{file_name}")
        ffmpeg.input(file_path, ss=start_time, to=end_time).output(trecho_path, format="mp3").run(
            overwrite_output=True)

        # Concatenar o áudio original com o trecho extra
        ffmpeg.concat(ffmpeg.input(file_path), ffmpeg.input(trecho_path), v=0, a=1).output(novo_path, format="mp3").run(
            overwrite_output=True)

        # Remover o arquivo temporário do trecho
        os.remove(trecho_path)

        # Obter duração do novo áudio
        from controllers.edicao_controller import EdicaoAudioController
        duracao_novo = EdicaoAudioService.obter_duracao_audio(novo_path)

        # Salvar o novo áudio no banco de dados
        novo_audio_id = EdicaoAudioService.salvar_audio_no_banco(novo_arquivo, novo_path, duracao_novo)

        # Associar ao projeto
        EdicaoAudioService.associar_audio_ao_projeto(project_id, novo_audio_id)
        HistoricoService.registrar_atividade(user_id, project_id, "edição", f"Alongou {file_name} com start-time {start_time} e end-time {end_time}")
        return {"status": "sucesso", "file_name": novo_arquivo, "file_path": novo_path}

    @staticmethod
    def encurtar_audio(project_id, file_name, start_time, end_time, user_id):
        """Remove um trecho de áudio entre `start_time` e `end_time`, reduzindo a duração total"""

        if not project_id or not file_name or start_time < 0 or end_time <= start_time:
            return {"status": "erro", "message": "Parâmetros inválidos."}

        # Buscar o arquivo no banco
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
                SELECT file_path FROM audio_files 
                JOIN projectos_audio_files ON audio_files.id = projectos_audio_files.audio_id 
                WHERE projectos_audio_files.project_id = %s AND audio_files.file_name = %s
            """, (project_id, file_name))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return {"status": "erro", "message": "Arquivo não encontrado para este projeto."}

        file_path = result[0]

        # Ajustar caminho do arquivo
        file_path = re.sub(r'^https?://localhost:\d+/', '', file_path)
        if not file_path.startswith(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file_path.lstrip("/"))

        if not os.path.exists(file_path):
            return {"status": "erro", "message": "Arquivo de áudio não encontrado."}

        # Obter duração total do áudio
        probe = ffmpeg.probe(file_path)
        duracao_total = float(probe['format']['duration'])

        if end_time > duracao_total:
            return {"status": "erro", "message": "O tempo de fim é maior que a duração do áudio."}

        # Criar novo nome de arquivo
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_base, file_ext = os.path.splitext(file_name)
        file_base = re.sub(r'^\d{14}_', '', file_base)  # Remover timestamp antigo
        novo_arquivo = f"{timestamp}_{file_base}{file_ext}"
        novo_path = os.path.join(UPLOAD_DIR, novo_arquivo)

        # Criar arquivos temporários para as partes antes e depois do corte
        parte1 = f"{UPLOAD_DIR}/{timestamp}_parte1.mp3"
        parte2 = f"{UPLOAD_DIR}/{timestamp}_parte2.mp3"

        # Extrair a parte antes do intervalo
        ffmpeg.input(file_path, t=start_time).output(parte1, format="mp3").run(overwrite_output=True)

        # Extrair a parte depois do intervalo (se houver)
        if end_time < duracao_total:
            ffmpeg.input(file_path, ss=end_time).output(parte2, format="mp3").run(overwrite_output=True)
        else:
            parte2 = None  # Se o corte for até o final, não há segunda parte

        # Concatenar as partes corretamente usando FFmpeg
        inputs = [ffmpeg.input(parte1)]
        if parte2:
            inputs.append(ffmpeg.input(parte2))

        (
            ffmpeg.concat(*inputs, v=0, a=1)
            .output(novo_path, format="mp3")
            .run(overwrite_output=True)
        )

        # Remover arquivos temporários
        os.remove(parte1)
        if parte2:
            os.remove(parte2)

        # Obter nova duração
        from controllers.edicao_controller import EdicaoAudioController
        duracao_novo = EdicaoAudioService.obter_duracao_audio(novo_path)

        # Salvar no banco de dados
        novo_audio_id = EdicaoAudioService.salvar_audio_no_banco(novo_arquivo, novo_path, duracao_novo)

        # Associar ao projeto
        EdicaoAudioService.associar_audio_ao_projeto(project_id, novo_audio_id)
        HistoricoService.registrar_atividade(user_id, project_id, "edição", f"Encurtou {file_name} com start-time {start_time} e end-time {end_time}")
        return {"status": "sucesso", "file_name": novo_arquivo, "file_path": novo_path}

    @staticmethod
    def aplicar_efeito(project_id, file_name, efeito, user_id):
        """Aplica um efeito de áudio, como reverb"""

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path FROM audio_files 
            JOIN projectos_audio_files ON audio_files.id = projectos_audio_files.audio_id 
            WHERE projectos_audio_files.project_id = %s AND audio_files.file_name = %s
        """, (project_id, file_name))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return {"status": "erro", "message": "Arquivo não encontrado para este projeto."}

        file_path = result[0]

        # Ajustar caminho
        file_path = re.sub(r'^https?://localhost:\d+/', '', file_path)
        if not file_path.startswith(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, file_path.lstrip("/"))

        if not os.path.exists(file_path):
            return {"status": "erro", "message": "Arquivo de áudio não encontrado."}

        # Criar novo nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_base, file_ext = os.path.splitext(file_name)
        file_base = re.sub(r'^\d{14}_', '', file_base)  # Remover timestamp antigo
        novo_arquivo = f"{timestamp}_{file_base}{file_ext}"
        novo_path = os.path.join(UPLOAD_DIR, novo_arquivo)

        # 🔥 Aplicar efeito de Reverb
        (
            ffmpeg
            .input(file_path)
            .filter("aecho", 0.8, 0.88, 60, 0.4)  # Efeito Reverb
            .output(novo_path, format="mp3")
            .run(overwrite_output=True)
        )

        # Obter duração do novo áudio
        duracao_novo = EdicaoAudioService.obter_duracao_audio(novo_path)

        # Salvar no banco de dados
        novo_audio_id = EdicaoAudioService.salvar_audio_no_banco(novo_arquivo, novo_path, duracao_novo)

        # Associar ao projeto
        EdicaoAudioService.associar_audio_ao_projeto(project_id, novo_audio_id)

        # Registrar no histórico de atividades
        HistoricoService.registrar_atividade(user_id, project_id, "edição",
                                             f"Aplicou efeito {efeito} no arquivo {file_name}")

        return {"status": "sucesso", "file_name": novo_arquivo, "file_path": novo_path}

    @staticmethod
    def salvar_audio_no_banco(file_name, file_path, duration):
        """ Insere o novo áudio na tabela audio_files e retorna o ID gerado """
        try:
            conn = database.conectar()
            cursor = conn.cursor()

            sql = "INSERT INTO audio_files (file_name, file_path, duration) VALUES (%s, %s, %s)"
            cursor.execute(sql, (file_name, file_path, duration))
            audio_id = cursor.lastrowid  # Obtém o ID do último insert

            conn.commit()
            cursor.close()
            conn.close()

            return audio_id
        except Exception as e:
            print(f"Erro ao salvar áudio no banco: {e}")
            return None

    @staticmethod
    def associar_audio_ao_projeto(project_id, audio_id):
        """ Associa um arquivo de áudio ao projeto """
        try:
            conn = database.conectar()
            cursor = conn.cursor()

            sql = "INSERT INTO projectos_audio_files (project_id, audio_id) VALUES (%s, %s)"
            cursor.execute(sql, (project_id, audio_id))

            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao associar áudio ao projeto: {e}")

    @staticmethod
    def obter_duracao_audio(file_path):
        """ Obtém a duração do áudio em segundos usando ffprobe """
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            return round(duration, 2)
        except Exception as e:
            print(f"Erro ao obter duração do áudio: {e}")
            return 0.0

    @staticmethod
    def excluir_audio(project_id, file_name, user_id):
        """Exclui um arquivo de áudio do sistema e do banco de dados"""

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

        # Ajustar caminho do arquivo
        file_path = re.sub(r'^https?://localhost:\d+/', '', file_path)
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

        # Registrar a exclusão no histórico
        HistoricoService.registrar_atividade(user_id, project_id, "exclusão", f"Arquivo {file_name} excluído")

        return {"status": "sucesso", "message": f"Arquivo {file_name} excluído com sucesso."}