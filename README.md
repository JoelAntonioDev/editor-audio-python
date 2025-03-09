# 🎵 PythonProject

Um projeto Python para manipulação e edição de arquivos de áudio, incluindo funcionalidades para alongar, encurtar e excluir arquivos de áudio.

## 🚀 Como configurar e executar o projeto

Siga os passos abaixo para clonar o repositório, instalar as dependências e executar o projeto corretamente.

### 🔹 1. Clonar o repositório

Abra o terminal (ou PowerShell) e execute:

    https://github.com/JoelAntonioDev/editor-audio-python.git
    cd PythonProject

### 🔹 2. Criar e ativar um ambiente virtual (recomendado)

Para evitar conflitos de dependências, crie um ambiente virtual Python:


        python -m venv .venv

Ative o ambiente virtual:
Windows (PowerShell):

        .\.venv\Scripts\Activate

Mac/Linux:

        source .venv/bin/activate

🔹 3. Instalar as dependências

Com o ambiente virtual ativado, instale as dependências:

        pip install -r requirements.txt

🔹 4. Configurar o banco de dados

A aplicação cria automaticamente o banco de dados jaudio2, caso ele ainda não exista. No entanto, é necessário garantir que as credenciais corretas do MySQL estejam configuradas.

No arquivo database.py, edite os seguintes parâmetros conforme necessário:

        config = {
            "host": "localhost",
            "user": "root",
            "password": "SUA_SENHA_AQUI",
        }

Se precisar alterar o nome do banco, modifique esta linha:

        config["database"] = "jaudio2"

Caso seu MySQL use uma porta diferente da padrão (3306), adicione:

        config["port"] = 3306  # Substitua pela porta correta

🔹 5. Configurar o FFmpeg

O projeto utiliza o FFmpeg para manipulação de áudio. Para garantir que funcione corretamente, adicione o FFmpeg às variáveis de ambiente do sistema.
✅ Windows:

No Explorador de Arquivos, copie o caminho onde está o FFmpeg, geralmente:

        C:\Users\SeuUsuario\Documents\PythonProject\PythonProject\ffmpeg\bin

No Windows, pressione Win + R, digite sysdm.cpl e pressione Enter.
Vá até a aba Avançado e clique em Variáveis de Ambiente.
Em Variáveis do sistema, encontre a variável Path, selecione e clique em Editar.
Clique em Novo e cole o caminho que copiou do FFmpeg:

        C:\Users\SeuUsuario\Documents\PythonProject\PythonProject\ffmpeg\bin

Clique em OK e reinicie o computador para aplicar as mudanças.

✅ macOS:

        Abra o terminal e instale o FFmpeg com:

        brew install ffmpeg

Verifique se está instalado corretamente:

        ffmpeg -version

Se necessário, adicione o caminho ao ~/.zshrc ou ~/.bashrc:

        echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
        source ~/.zshrc

✅ Linux (Ubuntu/Debian):

Instale o FFmpeg com:

        sudo apt update && sudo apt install ffmpeg -y

Verifique se está instalado corretamente:

ffmpeg -version

Se o comando ffmpeg não for encontrado, adicione o caminho manualmente ao ~/.bashrc:

        echo 'export PATH="/usr/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc

🔹 6. Executar o servidor

Agora, execute o projeto:

        python server.py

O servidor estará rodando! 🚀
📂 Estrutura do Projeto

📦 PythonProject
│-- 📂 controllers/        # Controladores da aplicação
│-- 📂 services/           # Serviços responsáveis pela lógica de negócio
│-- 📂 uploads/            # Arquivos de áudio enviados
│-- 📂 ffmpeg/             # Biblioteca FFmpeg para manipulação de áudio
│-- 📜 server.py           # Arquivo principal do servidor
│-- 📜 database.py         # Configuração do banco de dados
│-- 📜 requirements.txt    # Lista de dependências do projeto
│-- 📜 README.md           # Documentação do projeto

🛠 Dependências Principais

O projeto utiliza as seguintes bibliotecas:

    flask - Framework web para Python
    ffmpeg-python - Manipulação de áudio e vídeo
    mysql-connector-python - Conexão com MySQL
    dotenv - Carregamento de variáveis de ambiente
    json - Manipulação de dados em JSON