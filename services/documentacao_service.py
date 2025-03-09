
class DocumentacaoService:
    @staticmethod
    def gerar_documentacao_html(documentacao):
        """
        Gera um HTML formatado com a documentação da API.
        """
        html_content = """
        <!DOCTYPE html>
        <html lang="pt">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Documentação da API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; padding: 20px; background-color: #f4f4f4; }
                h1 { color: #333; }
                .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
                .endpoint { margin-bottom: 20px; padding: 10px; background: #e3e3e3; border-radius: 5px; }
                .method { font-weight: bold; color: #007BFF; }
                pre { background: #ddd; padding: 10px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📜 Documentação da API</h1>
        """

        for nome, descricao in documentacao.items():
            partes = descricao.split("\n\n")
            metodo_e_rota = partes[0].split(" ", 1) if len(partes) > 0 else ["", ""]
            metodo = metodo_e_rota[0]
            rota = metodo_e_rota[1] if len(metodo_e_rota) > 1 else ""

            html_content += f"""
            <div class="endpoint">
                <p><span class="method">{metodo}</span> <strong>{rota}</strong></p>
                <pre>{descricao.replace(metodo + ' ' + rota, '').strip()}</pre>
            </div>
            """

        html_content += """
            </div>
        </body>
        </html>
        """

        return html_content
