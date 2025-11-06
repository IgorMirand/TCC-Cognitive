import psycopg2
import bcrypt
import os
from psycopg2.errors import IntegrityError
import random 
import string  

class Database:
    def __init__(self):
        self.conn_string = os.environ.get("NEON_DB_URL")
        if not self.conn_string:
            raise ValueError("Variável de ambiente NEON_DB_URL não definida!")

        self.create_tables()

    def connect(self):
        # (5) Conecta-se ao Neon usando a string
        return psycopg2.connect(self.conn_string)

    def create_tables(self):
        # (6) É boa prática usar 'with' para gerir conexões e cursores
        with self.connect() as conn:
            with conn.cursor() as cursor:

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(20) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        user_type TEXT NOT NULL CHECK(user_type IN ('Paciente', 'Psicólogo')),
                        email TEXT UNIQUE NOT NULL, 
                        idade INT NOT NULL 
                    )
                ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS codigos_master
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   codigo
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   usado_por_user_id
                                   INT,
                                   FOREIGN
                                   KEY
                               (
                                   usado_por_user_id
                               ) REFERENCES users
                               (
                                   id
                               )
                                   )
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS codigos_paciente
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   codigo
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   gerado_por_psicologo_id
                                   INT
                                   NOT
                                   NULL,
                                   usado_por_paciente_id
                                   INT,
                                   FOREIGN
                                   KEY
                               (
                                   gerado_por_psicologo_id
                               ) REFERENCES users
                               (
                                   id
                               ),
                                   FOREIGN KEY
                               (
                                   usado_por_paciente_id
                               ) REFERENCES users
                               (
                                   id
                               )
                                   )
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS paciente_psicologo_link
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   paciente_user_id
                                   INT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   psicologo_user_id
                                   INT
                                   NOT
                                   NULL,
                                   FOREIGN
                                   KEY
                               (
                                   paciente_user_id
                               ) REFERENCES users
                               (
                                   id
                               ),
                                   FOREIGN KEY
                               (
                                   psicologo_user_id
                               ) REFERENCES users
                               (
                                   id
                               )
                                   )
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS atividades_diarias
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   user_id
                                   INT
                                   NOT
                                   NULL,
                                   atividade_texto
                                   TEXT
                                   NOT
                                   NULL,
                                   data
                                   TEXT
                                   NOT
                                   NULL,
                                   FOREIGN
                                   KEY
                               (
                                   user_id
                               ) REFERENCES users
                               (
                                   id
                               )
                                   )
                               ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS diario_paciente (
                        id SERIAL PRIMARY KEY,
                        user_id INT NOT NULL,
                        data_hora_iso TEXT NOT NULL,
                        anotacao TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS consultas_psicologo (
                        id SERIAL PRIMARY KEY,
                        psicologo_id INT NOT NULL,
                        paciente_id INT NOT NULL,
                        data_hora_iso TEXT NOT NULL,
                        anotacoes TEXT NOT NULL,
                        FOREIGN KEY (psicologo_id) REFERENCES users (id),
                        FOREIGN KEY (paciente_id) REFERENCES users (id)
                    )
                ''')

                # Opcional: Adiciona um código-mestre de teste
                try:
                    # (8) MUDANÇA SQL: Placeholders são %s em vez de ?
                    cursor.execute("INSERT INTO codigos_master (codigo) VALUES (%s)", ('MESTRE123',))
                except IntegrityError:
                    pass  # Código já existe

                # 'conn.commit()' é chamado automaticamente ao sair do bloco 'with'

    # --- FUNÇÕES DE VALIDAÇÃO DE CÓDIGO ---

    def validar_codigo_master(self, codigo):
        """Verifica se é um código-mestre válido e não usado."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM codigos_master WHERE codigo=%s AND usado_por_user_id IS NULL", (codigo,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
    
    def get_email_psicologo(self, id):
        try:    
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT email FROM users WHERE user_id=%s AND usado_por_user_id IS NULL",(id))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[ERRO] get_email_psicologo: {e}")
            return [] 

    def validar_codigo_paciente(self, codigo):
        """Verifica se é um código de paciente válido, não usado, e retorna o ID do psicólogo."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT gerado_por_psicologo_id FROM codigos_paciente WHERE codigo=%s AND usado_por_paciente_id IS NULL",
                    (codigo,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None

    # --- FUNÇÕES DE REGISTRO E VÍNCULO ---

    def register_user(self, username, password, user_type, email, idade):
        """Apenas regista o utilizador na tabela 'users'."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    password_hash_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    password_hash_str = password_hash_bytes.decode('utf-8')

                    # Adiciona email e idade ao INSERT
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, user_type, email, idade) 
                        VALUES (%s, %s, %s, %s, %s) 
                        RETURNING id
                        """,
                        (username, password_hash_str, user_type, email, idade)
                    )
                    user_id = cursor.fetchone()[0]

                    return True, "Usuário cadastrado com sucesso!", user_id

        except IntegrityError as e:
            # Verifica se a violação foi de 'username' ou 'email'
            if 'users_username_key' in str(e):
                return False, "Esse nome de usuário já existe.", None
            if 'users_email_key' in str(e):
                return False, "Esse email já está em uso.", None
            return False, "Usuário já existe.", None
        except Exception as e:
            return False, f"Erro inesperado: {e}", None

    def vincular_paciente_psicologo(self, paciente_id, psicologo_id):
        """Cria o vínculo na tabela 'paciente_psicologo_link'."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO paciente_psicologo_link (paciente_user_id, psicologo_user_id) VALUES (%s, %s)",
                        (paciente_id, psicologo_id)
                    )
                    return True
        except IntegrityError:
            return False

    def vincular_paciente_por_codigo(self, paciente_id, codigo):
        """
        Tenta vincular um paciente já existente a um psicólogo usando um código.
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    # 1. Verificar se o paciente já está vinculado
                    cursor.execute(
                        "SELECT id FROM paciente_psicologo_link WHERE paciente_user_id = %s",
                        (paciente_id,)
                    )
                    if cursor.fetchone():
                        return False, "Esta conta de paciente já está vinculada a um psicólogo."

                    # 2. Validar o código e obter o ID do psicólogo
                    # (Reutiliza a função que já temos!)
                    psicologo_id = self.validar_codigo_paciente(codigo)
                    
                    if not psicologo_id:
                        return False, "Código inválido, expirado ou já utilizado por outra pessoa."

                    # 3. Criar o vínculo (Reutiliza a função que já temos!)
                    self.vincular_paciente_psicologo(paciente_id, psicologo_id)

                    # 4. Marcar o código como usado (Reutiliza a função que já temos!)
                    self.marcar_codigo_paciente_usado(codigo, paciente_id)

                    return True, "Vínculo com o psicólogo realizado com sucesso!"

        except Exception as e:
            print(f"[ERRO] vincular_paciente_por_codigo: {e}")
            return False, "Um erro inesperado ocorreu."


    def marcar_codigo_master_usado(self, codigo_id, user_id):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE codigos_master SET usado_por_user_id = %s WHERE id = %s", (user_id, codigo_id))

    # --- FUNÇÃO DE LOGIN ---
    def verify_user(self, email, password):
        """Verifica o login e retorna o tipo de utilizador."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password_hash, user_type, id FROM users WHERE email=%s", (email,))
                user = cursor.fetchone()

                if user:
                    # user[0] é a STRING lida do DB (ex: '$2b$...')
                    # Codificamos a string do DB e a senha digitada para BYTES
                    hash_do_db_bytes = user[0].encode('utf-8')
                    senha_digitada_bytes = password.encode('utf-8')

                    if bcrypt.checkpw(senha_digitada_bytes, hash_do_db_bytes):
                        user_type = user[1]
                        user_id = user[2]
                        return True, "Login bem-sucedido!", user_type, user_id

                # Se 'user' for None ou o checkpw falhar
                return False, "Usuário ou senha inválidos.", None, None

    def add_atividades_diarias(self, user_id, lista_atividades, data_iso):
        """Salva uma lista de atividades para um utilizador específico numa data."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    dados_para_salvar = [
                        (user_id, texto, data_iso) for texto in lista_atividades
                    ]

                    # 'executemany' é ótimo para inserções em massa
                    cursor.executemany(
                        "INSERT INTO atividades_diarias (user_id, atividade_texto, data) VALUES (%s, %s, %s)",
                        dados_para_salvar
                    )
                    return True, "Atividades salvas com sucesso."

        except Exception as e:
            print(f"[ERRO] add_atividades_diarias: {e}")
            return False, "Erro ao salvar atividades."
        
    def add_anotacao_diario(self, user_id, anotacao_texto, data_hora_iso):
        """Salva uma nova anotação do diário para o paciente."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO diario_paciente (user_id, anotacao, data_hora_iso) VALUES (%s, %s, %s)",
                        (user_id, anotacao_texto, data_hora_iso)
                    )
                    return True, "Anotação salva com sucesso."
        except Exception as e:
            print(f"[ERRO] add_anotacao_diario: {e}")
            return False, "Erro ao salvar anotação."

    def get_anotacoes_diario(self, user_id):
        """Busca todas as anotações de um paciente, da mais nova para a mais antiga."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT data_hora_iso, anotacao FROM diario_paciente WHERE user_id = %s ORDER BY data_hora_iso DESC",
                        (user_id,)
                    )
                    return cursor.fetchall() # Retorna lista de tuplos (data, anotacao)
        except Exception as e:
            print(f"[ERRO] get_anotacoes_diario: {e}")
            return [] # Retorna lista vazia em caso de erro
        
    def add_anotacao_consulta(self, psicologo_id, paciente_id, anotacao_texto, data_hora_iso):
        """Salva a anotação da consulta no banco de dados."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO consultas_psicologo (psicologo_id, paciente_id, anotacoes, data_hora_iso) 
                        VALUES (%s, %s, %s, %s)
                        """,
                        (psicologo_id, paciente_id, anotacao_texto, data_hora_iso)
                    )
                    return True, "Anotação salva com sucesso."
        except Exception as e:
            print(f"[ERRO] add_anotacao_consulta: {e}")
            return False, "Erro ao salvar anotação."
        
    def get_pacientes_do_psicologo(self, psicologo_id):
        """Busca todos os pacientes vinculados a um psicólogo."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    # Busca na tabela de 'link' e junta com 'users'
                    # para pegar o ID e o NOME do paciente
                    cursor.execute(
                        """
                        SELECT U.id, U.username 
                        FROM paciente_psicologo_link AS L
                        JOIN users AS U ON L.paciente_user_id = U.id
                        WHERE L.psicologo_user_id = %s
                        """,
                        (psicologo_id,)
                    )
                    return cursor.fetchall() # Retorna lista de tuplos (id, username)
        except Exception as e:
            print(f"[ERRO] get_pacientes_do_psicologo: {e}")
            return [] # Retorna lista vazia em caso de erro
    
    def gerar_codigo_paciente(self, psicologo_id):
        """
        Gera um código de 6 dígitos (XXX-XXX), salva-o, e retorna-o.
        """
        # Define os caracteres a usar (Letras Maiúsculas + Números)
        alfanumerico = string.ascii_uppercase + string.digits
        
        while True: 
            # (Looping caso, por uma rara coincidência, o código já exista)
            try:
                # Gera o código (ex: "A4T-K9P")
                parte1 = ''.join(random.choices(alfanumerico, k=3))
                parte2 = ''.join(random.choices(alfanumerico, k=3))
                novo_codigo = f"{parte1}-{parte2}"

                with self.connect() as conn:
                    with conn.cursor() as cursor:
                        # Insere o novo código na tabela, associado ao psicólogo
                        cursor.execute(
                            """
                            INSERT INTO codigos_paciente (codigo, gerado_por_psicologo_id)
                            VALUES (%s, %s)
                            """,
                            (novo_codigo, psicologo_id)
                        )
                        print(f"Código gerado: {novo_codigo} para psicólogo ID: {psicologo_id}")
                        return novo_codigo # Sucesso! Retorna o código para a app

            except IntegrityError:
                # Ocorreu uma colisão (código já existe). O loop tentará novamente.
                print(f"Colisão de código detectada ({novo_codigo}). Gerando novo...")
                continue 
            
            except Exception as e:
                print(f"[ERRO] gerar_codigo_paciente: {e}")
                return None # Falha