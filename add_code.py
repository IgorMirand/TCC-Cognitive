import os
import string
import psycopg2
import random
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class MasterCodeManager:
    def __init__(self):
        # Pega a string de conexão ao iniciar a classe
        self.conn_string = os.environ.get("NEON_DB_URL")
        if not self.conn_string:
            raise ValueError("Variável de ambiente NEON_DB_URL não definida!")

    def connect(self):
        """Conecta-se ao Neon usando a string armazenada"""
        return psycopg2.connect(self.conn_string)

    def gerar_codigo_master(self):
        """
        Gera um código, tenta salvar no banco e retorna (Sucesso, Mensagem/Código).
        """
        conn = None
        try:
            # Geração do código
            alfanumerico = string.ascii_uppercase + string.digits
            parte1 = ''.join(random.choices(alfanumerico, k=4))
            parte2 = ''.join(random.choices(alfanumerico, k=4))
            novo_codigo = f"{parte1}-{parte2}"

            # Conexão e inserção
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    query = "INSERT INTO codigos_master (codigo) VALUES (%s) RETURNING id"
                    
                    cursor.execute(query, (novo_codigo,))
                    new_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    return True, novo_codigo, f"Código mestre '{novo_codigo}' adicionado com ID {new_id}."

        except psycopg2.IntegrityError:
            if conn: conn.rollback()
            return False, None, "Erro: Esse código mestre já existe (colisão gerada, tente novamente)."
        
        except Exception as e:
            if conn: conn.rollback()
            return False, None, f"Erro inesperado: {e}"

    def inserir_codigo_mestre(self):
        """Função principal que chama a geração e exibe o resultado"""
        try:
            # Chama a função que gera e salva
            sucesso, codigo, mensagem = self.gerar_codigo_master()
            
            if sucesso:
                print(f"[SUCESSO] {mensagem}")
                print(f"--> Código para uso: {codigo}")
            else:
                print(f"[FALHA] {mensagem}")

        except Exception as e:
            print(f"Uma falha crítica ocorreu: {e}")

# --- Execução ---
if __name__ == "__main__":
    # 1. Instancia a classe (Cria o objeto)
    manager = MasterCodeManager() 
    # 2. Chama o método do objeto
    manager.inserir_codigo_mestre()