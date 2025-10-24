import psycopg2
import bcrypt
from psycopg2.errors import IntegrityError

DATABASE_URL = "postgresql://neondb_owner:npg_8ByXDGdvfV9g@ep-solitary-hall-adcolek9-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

class Database:
    def __init__(self):
        # (4) Lê a connection string do ambiente
        self.conn_string = DATABASE_URL
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

                # (7) MUDANÇA SQL: SERIAL PRIMARY KEY é o 'AUTOINCREMENT' do PostgreSQL
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS users
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   username
                                   TEXT
                                   UNIQUE
                                   NOT
                                   NULL,
                                   password_hash
                                   TEXT
                                   NOT
                                   NULL,
                                   user_type
                                   TEXT
                                   NOT
                                   NULL
                                   CHECK (
                                   user_type
                                   IN
                               (
                                   'Paciente',
                                   'Psicólogo'
                               ))
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

    def register_user(self, username, password, user_type):
        """Apenas regista o utilizador na tabela 'users'."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    password_hash_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    password_hash_str = password_hash_bytes.decode('utf-8')

                    cursor.execute(
                        "INSERT INTO users (username, password_hash, user_type) VALUES (%s, %s, %s) RETURNING id",
                        (username, password_hash_str, user_type)
                    )
                    user_id = cursor.fetchone()[0]

                    return True, "Usuário cadastrado com sucesso!", user_id

        except IntegrityError:
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
        except IntegrityError:  # Paciente já vinculado
            return False

    def marcar_codigo_master_usado(self, codigo_id, user_id):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE codigos_master SET usado_por_user_id = %s WHERE id = %s", (user_id, codigo_id))

    def marcar_codigo_paciente_usado(self, codigo, user_id):
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE codigos_paciente SET usado_por_paciente_id = %s WHERE codigo = %s",
                               (user_id, codigo))

    # --- FUNÇÃO DE LOGIN ---

    def verify_user(self, username, password):
        """Verifica o login e retorna o tipo de utilizador."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password_hash, user_type, id FROM users WHERE username=%s", (username,))
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