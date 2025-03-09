import mysql.connector

def conectar(usando_banco=True):
    config = {
        "host": "localhost",
        "user": "root",
        "password": "J12l34@gmail.com",
    }
    if usando_banco:
        config["database"] = "jaudio2"  # Se o banco já existir, conecta nele

    return mysql.connector.connect(**config)

def criar_banco():
    # Conectar sem o banco para criar o banco 'jaudio2'
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="J12l34@gmail.com"
    )
    cursor = conexao.cursor()

    # Cria o banco de dados se não existir
    cursor.execute("CREATE DATABASE IF NOT EXISTS jaudio2")
    print("Banco de dados 'jaudio2' criado com sucesso!")

    cursor.close()
    conexao.close()

def criar_tabelas():
    conexao = conectar()
    cursor = conexao.cursor()

    # SQL para criar as tabelas
    tabelas = [
        """
        CREATE TABLE IF NOT EXISTS audio_files (
            id BIGINT NOT NULL AUTO_INCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            duration DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS audio_edits (
            id BIGINT NOT NULL AUTO_INCREMENT,
            audio_id BIGINT DEFAULT NULL,
            edit_type ENUM('cortar','alongar','encurtar') NOT NULL,
            start_time DECIMAL(10,2) NOT NULL,
            end_time DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY audio_id (audio_id),
            CONSTRAINT audio_edits_ibfk_1 FOREIGN KEY (audio_id) REFERENCES audio_files (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT NOT NULL AUTO_INCREMENT,
            nome VARCHAR(255) NOT NULL,
            sobrenome VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            senha TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            admin TINYINT(1) DEFAULT '0',
            PRIMARY KEY (id),
            UNIQUE KEY email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS projectos (
            id BIGINT NOT NULL AUTO_INCREMENT,
            project_name VARCHAR(255) NOT NULL,
            user_id INT DEFAULT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            CONSTRAINT projectos_ibfk_1 FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS projectos_audio_files (
          project_id bigint NOT NULL,
          audio_id bigint NOT NULL,
          PRIMARY KEY (project_id,audio_id),
          KEY audio_id (audio_id),
          CONSTRAINT projectos_audio_files_ibfk_1 FOREIGN KEY (project_id) REFERENCES projectos (id) ON DELETE CASCADE,
          CONSTRAINT projectos_audio_files_ibfk_2 FOREIGN KEY (audio_id) REFERENCES audio_files (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
            """
        CREATE TABLE IF NOT EXISTS historico_atividades (
            id BIGINT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            projeto_id BIGINT DEFAULT NULL,
            tipo_atividade VARCHAR(255) NOT NULL,
            descricao TEXT NOT NULL,
            timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            KEY projeto_id (projeto_id),
            CONSTRAINT historico_atividades_ibfk_1 FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE,
            CONSTRAINT historico_atividades_ibfk_2 FOREIGN KEY (projeto_id) REFERENCES projectos (id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS rascunhos (
            id BIGINT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            projeto_id BIGINT DEFAULT NULL,
            audio_id BIGINT DEFAULT NULL,
            descricao TEXT,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            KEY projeto_id (projeto_id),
            KEY audio_id (audio_id),
            CONSTRAINT rascunhos_ibfk_1 FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE,
            CONSTRAINT rascunhos_ibfk_2 FOREIGN KEY (projeto_id) REFERENCES projectos (id) ON DELETE SET NULL,
            CONSTRAINT rascunhos_ibfk_3 FOREIGN KEY (audio_id) REFERENCES audio_files (id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS registros_login (
            id BIGINT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            timestamp TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            CONSTRAINT registros_login_ibfk_1 FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """,
        """
        CREATE TABLE IF NOT EXISTS sessoes (
            id BIGINT NOT NULL AUTO_INCREMENT,
            user_id INT NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            token TEXT NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NULL DEFAULT NULL,
            PRIMARY KEY (id),
            KEY user_id (user_id),
            CONSTRAINT sessoes_ibfk_1 FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
        """
    ]

    # Executar a criação de tabelas
    for tabela in tabelas:
        cursor.execute(tabela)
        print("Tabela criada com sucesso!")

    cursor.close()
    conexao.close()


