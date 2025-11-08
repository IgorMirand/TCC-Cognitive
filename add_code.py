from app.core.neon import Database  # Importa sua classe Database do arquivo neon.py
from dotenv import load_dotenv

load_dotenv() 
# -------------------------------------------------------------------

def inserir_codigo_mestre():
    try:
        # 1. Conecta ao banco de dados
        # (A classe Database vai ler a NEON_DB_URL sozinha)
        db = Database()
        novo_codigo = db.add_codigo_master()
        
        # 3. Mostra o resultado
        print(f"iserido novo o código mestre: '{novo_codigo}'...")

    except Exception as e:
        print(f"Uma falha inesperada ocorreu: {e}")

# Isso faz o script rodar quando chamado pelo terminal
if __name__ == "__main__":
    inserir_codigo_mestre()