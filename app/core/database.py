import sqlite3
import bcrypt

class Database:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.create_tables()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        conn = self.connect()
        cursor = conn.cursor()

        # Tabela 1: Armazena todas as contas
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
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

        # Tabela 2: Códigos para CRIAR contas de Psicólogo
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS codigos_master
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           codigo
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           usado_por_user_id
                           INTEGER,
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

        # Tabela 3: Códigos para VINCULAR Pacientes (gerados por Psicólogos)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS codigos_paciente
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           codigo
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           gerado_por_psicologo_id
                           INTEGER
                           NOT
                           NULL,
                           usado_por_paciente_id
                           INTEGER,
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

        # Tabela 4: O VÍNCULO (Sua ideia: 1 Paciente -> 1 Psicólogo)
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS paciente_psicologo_link
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           paciente_user_id
                           INTEGER
                           UNIQUE
                           NOT
                           NULL,
                           psicologo_user_id
                           INTEGER
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

        # Armazena cada atividade feita por um utilizador num certo dia
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS atividades_diarias
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           user_id
                           INTEGER
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
            cursor.execute("INSERT INTO codigos_master (codigo) VALUES ('MESTRE123')")
        except sqlite3.IntegrityError:
            pass  # Código já existe

        conn.commit()
        conn.close()

    # --- FUNÇÕES DE VALIDAÇÃO DE CÓDIGO ---

    def validar_codigo_master(self, codigo):
        """Verifica se é um código-mestre válido e não usado."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM codigos_master WHERE codigo=? AND usado_por_user_id IS NULL", (codigo,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else None  # Retorna o ID do código

    def validar_codigo_paciente(self, codigo):
        """Verifica se é um código de paciente válido, não usado, e retorna o ID do psicólogo."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT gerado_por_psicologo_id FROM codigos_paciente WHERE codigo=? AND usado_por_paciente_id IS NULL",
            (codigo,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else None  # Retorna o ID do psicólogo

    # --- FUNÇÕES DE REGISTRO E VÍNCULO ---

    def register_user(self, username, password, user_type):
        """Apenas registra o usuário na tabela 'users'."""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            cursor.execute(
                "INSERT INTO users (username, password_hash, user_type) VALUES (?, ?, ?)",
                (username, password_hash, user_type)
            )
            user_id = cursor.lastrowid  # Pega o ID do usuário recém-criado
            conn.commit()
            conn.close()
            return True, "Usuário cadastrado com sucesso!", user_id

        except sqlite3.IntegrityError:
            conn.close()
            return False, "Usuário já existe.", None
        except Exception as e:
            conn.close()
            return False, f"Erro inesperado: {e}", None

    def vincular_paciente_psicologo(self, paciente_id, psicologo_id):
        """Cria o vínculo na tabela 'paciente_psicologo_link'."""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO paciente_psicologo_link (paciente_user_id, psicologo_user_id) VALUES (?, ?)",
                (paciente_id, psicologo_id)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:  # Paciente já vinculado
            return False

    def marcar_codigo_master_usado(self, codigo_id, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE codigos_master SET usado_por_user_id = ? WHERE id = ?", (user_id, codigo_id))
        conn.commit()
        conn.close()

    def marcar_codigo_paciente_usado(self, codigo, user_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE codigos_paciente SET usado_por_paciente_id = ? WHERE codigo = ?", (user_id, codigo))
        conn.commit()
        conn.close()

    # --- FUNÇÃO DE LOGIN ---

    def verify_user(self, username, password):
        """Verifica o login e retorna o tipo de usuário."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, user_type, id FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
            user_type = user[1]
            user_id = user[2]
            return True, "Login bem-sucedido!", user_type, user_id
        else:
            return False, "Usuário ou senha inválidos.", None, None

    # (get_user_id pode ser removido, pois verify_user já retorna o ID)

    def add_atividades_diarias(self, user_id, lista_atividades, data_iso):
        """
        Salva uma lista de atividades para um utilizador específico numa data.
        Usa uma transação para garantir que todas sejam salvas juntas.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Prepara os dados para inserção em massa
            # (user_id, "Texto da Atividade 1", "2025-10-21")
            # (user_id, "Texto da Atividade 2", "2025-10-21")
            dados_para_salvar = [
                (user_id, texto, data_iso) for texto in lista_atividades
            ]

            # Executa a inserção em massa
            cursor.executemany(
                "INSERT INTO atividades_diarias (user_id, atividade_texto, data) VALUES (?, ?, ?)",
                dados_para_salvar
            )
            conn.commit()
            conn.close()
            return True, "Atividades salvas com sucesso."

        except Exception as e:
            conn.close()
            print(f"[ERRO] add_atividades_diarias: {e}")
            return False, "Erro ao salvar atividades."