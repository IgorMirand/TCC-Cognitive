import psycopg2
import bcrypt
import os
from psycopg2.errors import IntegrityError
import random 
import string  
import pytz 
from datetime import datetime

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
                        data_nacimento DATE NOT NULL 
                    );
                ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS codigos_master(
                                    id  SERIAL PRIMARY KEY,
                                    codigo TEXT UNIQUE NOT NULL,
                                    usado_por_user_id  INT,
                                    FOREIGN KEY (usado_por_user_id ) REFERENCES users (id)
                                );
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS codigos_paciente (
                                    id SERIAL PRIMARY  KEY,
                                    codigo TEXT UNIQUE NOT NULL,
                                    gerado_por_psicologo_id INT NOT NULL,
                                    usado_por_paciente_id INT,
                                    FOREIGN KEY (gerado_por_psicologo_id) REFERENCES users (id),
                                    FOREIGN KEY (usado_por_paciente_id)  REFERENCES users(id)
                                );
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS paciente_psicologo_link(
                                    id SERIAL PRIMARY KEY,
                                    paciente_user_id INT UNIQUE NOT NULL,
                                    psicologo_user_id INT NOT NULL,
                                    FOREIGN KEY (paciente_user_id) REFERENCES users (id),
                                    FOREIGN KEY (psicologo_user_id) REFERENCES users (id)
                                );
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS atividades_template (
                                    id SERIAL PRIMARY KEY,
                                    atividade_texto TEXT NOT NULL,
                                    criado_por_psicologo_id INT NOT NULL,
                                    FOREIGN KEY (criado_por_psicologo_id) REFERENCES users (id)
                               );
                               ''')
                
                cursor.execute('''
                                CREATE TABLE IF NOT EXISTS entradas_diario (
                                    id SERIAL PRIMARY KEY,
                                    paciente_id INT NOT NULL REFERENCES users(id),
                                    data_hora_iso TEXT NOT NULL,
                                    sentimento_id INT NOT NULL, -- (1 para Feliz, 2 para Triste, etc.)
                                    anotacao TEXT -- A nota de texto livre
                                );
                            ''')
                                        
                cursor.execute('''
                                CREATE TABLE IF NOT EXISTS registros_atividades_diario (
                                    id SERIAL PRIMARY KEY,
                                    entrada_diario_id INT NOT NULL REFERENCES entradas_diario(id) ON DELETE CASCADE,
                                    atividade_template_id INT NOT NULL REFERENCES atividades_template(id)
                                );
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
                                );
                            ''')
                cursor.execute("""
                                CREATE TABLE IF NOT EXISTS agenda (
                                    id SERIAL PRIMARY KEY,
                                    psicologo_id INT NOT NULL,
                                    paciente_id INT, -- Se NULL, está livre
                                    data_hora TIMESTAMP NOT NULL,
                                    UNIQUE(psicologo_id, data_hora)
                                );
                            """)

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
    def register_user(self, username, password, user_type, email, data_nascimento_str):
        """
        Registra o usuário convertendo a data DD/MM/YYYY para YYYY-MM-DD (Postgres).
        """
        try:
            # Converte "25/12/1990" para "1990-12-25"
            data_obj = datetime.strptime(data_nascimento_str, "%d/%m/%Y")
            data_iso = data_obj.strftime("%Y-%m-%d")

            with self.connect() as conn:
                with conn.cursor() as cursor:
                    password_hash_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    password_hash_str = password_hash_bytes.decode('utf-8')

                    # CORRIGIDO: Usa data_nacimento em vez de idade
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, user_type, email, data_nacimento) 
                        VALUES (%s, %s, %s, %s, %s) 
                        RETURNING id
                        """,
                        (username, password_hash_str, user_type, email, data_iso)
                    )
                    user_id = cursor.fetchone()[0]
                    return True, "Usuário cadastrado com sucesso!", user_id

        except IntegrityError as e:
            print(f"⚠️ ERRO REAL DO BANCO: {e}")  # <--- ADICIONE ISSO
            
            if 'users_username_key' in str(e):
                return False, "Esse nome de usuário já existe.", None
            if 'users_email_key' in str(e):
                return False, "Esse email já está em uso.", None
            return False, "Usuário já existe.", None
        except ValueError:
             return False, "Formato de data inválido.", None
        except Exception as e:
            print(f"[ERRO] register_user: {e}")
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

    def get_patient_count(self, psicologo_id):
        """Conta quantos pacientes um psicólogo tem."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(id) FROM paciente_psicologo_link WHERE psicologo_user_id = %s",
                        (psicologo_id,)
                    )
                    count = cursor.fetchone()[0]
                    return True, count
        except Exception as e:
            print(f"[ERRO] get_patient_count: {e}")
            return False, 0

    def get_next_appointment(self, psicologo_id):
        """Busca a próxima consulta agendada (do futuro) e o nome do paciente."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    # Query que busca a consulta futura mais próxima
                    # E junta com a tabela 'users' para pegar o nome do paciente
                    query = """
                        SELECT 
                            C.data_hora_iso, 
                            U.username 
                        FROM 
                            consultas_psicologo AS C
                        JOIN 
                            users AS U ON C.paciente_id = U.id
                        WHERE 
                            C.psicologo_id = %s AND C.data_hora_iso > %s
                        ORDER BY 
                            C.data_hora_iso ASC
                        LIMIT 1
                    """
                    # Pega o timestamp atual para filtrar só consultas futuras
                    agora_iso = datetime.now(pytz.utc).isoformat()
                    
                    cursor.execute(query, (psicologo_id, agora_iso))
                    proxima_consulta = cursor.fetchone() # (data, nome_paciente)
                    
                    return True, proxima_consulta # Retorna a tupla ou None
        except Exception as e:
            print(f"[ERRO] get_next_appointment: {e}")
            return False, None

    def marcar_codigo_paciente_usado(self, codigo, paciente_id):
        """Marca o código de paciente como utilizado no banco de dados."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE codigos_paciente SET usado_por_paciente_id = %s WHERE codigo = %s", 
                        (paciente_id, codigo)
                    )
                    # O commit acontece automaticamente ao sair do bloco 'with', 
                    # mas se quiser garantir, o psycopg2 faz no fechamento da conexão.
        except Exception as e:
            print(f"[ERRO] marcar_codigo_paciente_usado: {e}")

    def marcar_codigo_master_usado(self, codigo_id, user_id):
            """
            Marca o código mestre como usado pelo psicólogo recém-criado.
            """
            try:
                with self.connect() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE codigos_master SET usado_por_user_id = %s WHERE id = %s",
                            (user_id, codigo_id)
                        )
                        # O commit é automático ao sair do bloco with
                        return True
            except Exception as e:
                print(f"[ERRO] marcar_codigo_master_usado: {e}")
                return False

    # --- FUNÇÃO DE LOGIN ---
    def verify_user(self, email, password):
        """Verifica o login e retorna o tipo de utilizador."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT password_hash, user_type, id, username FROM users WHERE email=%s", (email,))
                user = cursor.fetchone()

                if user:
                    # user[0] é a STRING lida do DB (ex: '$2b$...')
                    # Codificamos a string do DB e a senha digitada para BYTES
                    hash_do_db_bytes = user[0].encode('utf-8')
                    senha_digitada_bytes = password.encode('utf-8')

                    if bcrypt.checkpw(senha_digitada_bytes, hash_do_db_bytes):
                        user_type = user[1]
                        user_id = user[2]
                        username = user[3]

                        return True, "Login bem-sucedido!", user_type, user_id, username

                # Se 'user' for None ou o checkpw falhar
                return False, "Usuário ou senha inválidos.", None, None

    # --- FLUXO DE ATIVIDADES (M:N) ---
    def adicionar_atividade_template(self, atividade_texto, psicologo_id):
        """
        Adiciona uma nova atividade global.
        Verifica duplicatas e requer o ID do psicólogo (obrigatório no seu banco).
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    # 1. Verifica se já existe uma atividade com esse nome exato
                    # (Isso evita ter 10 atividades chamadas "Yoga")
                    cursor.execute(
                        "SELECT id FROM atividades_template WHERE atividade_texto = %s", 
                        (atividade_texto,)
                    )
                    if cursor.fetchone():
                        return False, "Esta atividade já existe no sistema."

                    # 2. Insere a nova atividade vinculada ao psicólogo
                    query = """
                        INSERT INTO atividades_template (atividade_texto, criado_por_psicologo_id) 
                        VALUES (%s, %s)
                    """
                    cursor.execute(query, (atividade_texto, psicologo_id))
                    
                    # O commit é automático pelo 'with self.connect()'
                    return True, f"Atividade '{atividade_texto}' criada com sucesso!"

        except Exception as e:
            print(f"[ERRO] adicionar_atividade_template: {e}")
            return False, "Erro interno ao salvar atividade."

    def delete_atividade_template(self, atividade_id):
            """Remove uma atividade da lista global."""
            try:
                with self.connect() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM atividades_template WHERE id = %s", (atividade_id,))
                        return True, "Atividade excluída com sucesso."
            except IntegrityError:
                # O banco impede excluir se algum paciente já usou essa atividade no diário
                return False, "Não é possível excluir: esta atividade já está sendo usada em diários de pacientes."
            except Exception as e:
                print(f"[ERRO] delete_atividade: {e}")
                return False, "Erro ao excluir."

    def update_atividade_template(self, atividade_id, novo_nome):
        """Atualiza o nome de uma atividade existente."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE atividades_template SET atividade_texto = %s WHERE id = %s",
                        (novo_nome, atividade_id)
                    )
                    return True, "Atividade atualizada."
        except Exception as e:
            print(f"[ERRO] update_atividade: {e}")
            return False, "Erro ao atualizar."

    def get_atividades_template(self):
        """
        (Substitui 'get_atividades_disponiveis')
        Busca todos os modelos de atividades (ID e Texto) para o paciente escolher.
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, atividade_texto FROM atividades_template")
                    # Retorna uma lista de tuplas, ex: [(1, 'Meditar'), (2, 'Correr')]
                    return True, cursor.fetchall()
        except Exception as e:
            print(f"[ERRO] get_atividades_template: {e}")
            return False, []
    
    def add_entrada_completa_diario(self, paciente_id, data_hora_iso, sentimento_id, anotacao, lista_de_ids_atividades):
        try:
            # 'with' gerencia a conexão, commit e rollback
            with self.connect() as conn: 
                with conn.cursor() as cursor:

                    # Passo 1: Inserir a entrada "mestre"
                    query_mestre = """
                        INSERT INTO entradas_diario (paciente_id, data_hora_iso, sentimento_id, anotacao)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """
                    cursor.execute(query_mestre, (paciente_id, data_hora_iso, sentimento_id, anotacao))
                    nova_entrada_id = cursor.fetchone()[0]

                    # Passo 2: Inserir as atividades "detalhe"
                    if lista_de_ids_atividades:
                        from psycopg2.extras import execute_values
                        dados_atividades = [(nova_entrada_id, atividade_id) for atividade_id in lista_de_ids_atividades]
                        query_detalhe = """
                            INSERT INTO registros_atividades_diario (entrada_diario_id, atividade_template_id) 
                            VALUES %s
                        """
                        execute_values(cursor, query_detalhe, dados_atividades)

                    # 'conn.commit()' é chamado automaticamente aqui se não houver erro
                    return True, "Diário salvo com sucesso."

        except Exception as e:
            # 'conn.rollback()' é chamado automaticamente aqui se houver erro
            print(f"[ERRO] add_entrada_completa_diario: {e}")
            return False, f"Erro ao salvar diário: {e}"
        # 'conn.close()' é chamado automaticamente ao sair do 'with'

    def get_entradas_historico(self, paciente_id):
        """
        Busca o histórico completo do diário, agregando as atividades.
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT
                            E.id,
                            E.data_hora_iso,
                            E.sentimento_id,
                            E.anotacao,
                            STRING_AGG(T.atividade_texto, ', ') AS atividades_agregadas
                        FROM
                            entradas_diario AS E
                        LEFT JOIN
                            registros_atividades_diario AS R ON E.id = R.entrada_diario_id
                        LEFT JOIN
                            atividades_template AS T ON R.atividade_template_id = T.id
                        WHERE
                            E.paciente_id = %s
                        GROUP BY
                            E.id, E.data_hora_iso, E.sentimento_id, E.anotacao
                        ORDER BY
                            E.data_hora_iso DESC;
                    """
                    cursor.execute(query, (paciente_id,))
                    # Retorna: [(id, data, sentimento_id, anotacao, "Correr, Meditar"), ...]
                    return True, cursor.fetchall()
        except Exception as e:
            print(f"[ERRO] get_entradas_historico: {e}")
            return False, []

    def salvar_anotacao_psicologo(self, psicologo_id, paciente_id, anotacao_texto, data_hora_iso):
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
        
    def get_anotacoes_paciente(self, psicologo_id, paciente_id):
        """Retorna todas as anotações do psicólogo para um paciente específico."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, data_hora_iso, anotacoes
                        FROM consultas_psicologo
                        WHERE psicologo_id = %s AND paciente_id = %s
                        ORDER BY data_hora_iso DESC;
                    """, (psicologo_id, paciente_id))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[ERRO] get_anotacoes_paciente: {e}")
            return []

    def get_pacientes_do_psicologo_com_nomes(self, psicologo_id):
        """
        Retorna uma lista de tuplas (id_paciente, nome_paciente)
        para o psicólogo selecionar.
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT p.paciente_user_id, u.username
                        FROM paciente_psicologo_link p
                        JOIN users u ON p.paciente_user_id = u.id
                        WHERE p.psicologo_user_id = %s
                        ORDER BY u.username ASC;
                    """, (psicologo_id,))
                    return cursor.fetchall()
        except Exception as e:
            print(f"[ERRO] get_pacientes_do_psicologo_com_nomes: {e}")
            return []

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
                
    def gerar_codigo_master(self):
            """
            Adiciona um novo código mestre (criado por um admin) ao banco de dados.
            """
            try:
                
                alfanumerico = string.ascii_uppercase + string.digits
                parte1 = ''.join(random.choices(alfanumerico, k=4))
                parte2 = ''.join(random.choices(alfanumerico, k=4))
                novo_codigo = f"{parte1}-{parte2}"

                novo_codigo = f"{parte1}-{parte2}"
                with self.connect() as conn:
                    with conn.cursor() as cursor:
                        query = "INSERT INTO codigos_master (codigo) VALUES (%s) RETURNING id"
                        
                        # Usa (novo_codigo,) para criar uma tupla
                        cursor.execute(query, (novo_codigo,))
                        
                        new_id = cursor.fetchone()[0]
                        conn.commit()
                        return True, f"Código mestre '{novo_codigo}' adicionado com ID {new_id}."

            except IntegrityError: # Pega a violação da restrição UNIQUE
                if conn: conn.rollback()
                return False, "Erro: Esse código mestre já existe."
            
            except Exception as e:
                if conn: conn.rollback()
                print(f"[ERRO] add_codigo_master: {e}")
                return False, f"Erro inesperado: {e}"

    def adicionar_disponibilidade(self, psicologo_id, data_hora_iso):
            """Psicólogo adiciona um horário livre."""
            try:
                with self.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO agenda (psicologo_id, data_hora, paciente_id)
                            VALUES (%s, %s, NULL)
                        """, (psicologo_id, data_hora_iso))
                        conn.commit()
                    return True, "Horário adicionado!"
            except Exception as e:
                return False, f"Erro ao adicionar (talvez já exista): {e}"

    def get_agenda_psicologo(self, psicologo_id):
        """Retorna toda a agenda do psicólogo (livres e ocupados)."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, data_hora, paciente_id 
                    FROM agenda 
                    WHERE psicologo_id = %s AND data_hora >= NOW()
                    ORDER BY data_hora ASC
                """, (psicologo_id,))
                return cursor.fetchall()

    def get_horarios_disponiveis(self, psicologo_id):
        """Retorna apenas horários LIVRES para o paciente ver."""
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, data_hora 
                    FROM agenda 
                    WHERE psicologo_id = %s AND paciente_id IS NULL AND data_hora >= NOW()
                    ORDER BY data_hora ASC
                """, (psicologo_id,))
                return cursor.fetchall()

    def agendar_consulta(self, agenda_id, paciente_id):
        """Paciente reserva um horário."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE agenda 
                        SET paciente_id = %s 
                        WHERE id = %s AND paciente_id IS NULL
                    """, (paciente_id, agenda_id))
                    
                    if cursor.rowcount == 0:
                        return False, "Horário não está mais disponível."
                    
                    conn.commit()
                return True, "Consulta agendada com sucesso!"
        except Exception as e:
            return False, str(e)
            
    def excluir_horario(self, agenda_id):
        """Psicólogo remove um horário (apenas se não tiver consulta marcada, opcional)."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM agenda WHERE id = %s", (agenda_id,))
                    conn.commit()
                return True, "Horário removido."
        except Exception as e:
            return False, str(e)

    def get_psicologo_id_by_paciente(self, paciente_id):
            
            """
            Retorna o ID do psicólogo vinculado ao paciente fornecido.
            Usado para saber qual agenda mostrar para o paciente.
            """
            try:
                with self.connect() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT psicologo_user_id FROM paciente_psicologo_link WHERE paciente_user_id = %s",
                            (paciente_id,)
                        )
                        resultado = cursor.fetchone()
                        
                        # Se encontrar registro, retorna o ID (resultado[0]), senão retorna None
                        return resultado[0] if resultado else None
                        
            except Exception as e:
                print(f"[ERRO] get_psicologo_id_by_paciente: {e}")
                return None
            
    def get_user_details(self, user_id):
        """Busca os detalhes editáveis de um usuário (nome, email, data_nasc)."""
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT username, email, data_nacimento FROM users WHERE id = %s",
                        (user_id,)
                    )
                    # Retorna (username, email, <datetime.date object>)
                    return cursor.fetchone() 
        except Exception as e:
            print(f"[ERRO] get_user_details: {e}")
            return None

    def update_user_details(self, user_id, username, email, data_nascimento_str):
        """
        Atualiza os dados do usuário.
        Converte a data DD/MM/YYYY para YYYY-MM-DD (Postgres).
        """
        try:
            # Converte "25/12/1990" para "1990-12-25"
            data_obj = datetime.strptime(data_nascimento_str, "%d/%m/%Y")
            data_iso = data_obj.strftime("%Y-%m-%d")

            with self.connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE users 
                        SET username = %s, email = %s, data_nacimento = %s
                        WHERE id = %s
                        """,
                        (username, email, data_iso, user_id)
                    )
                    # conn.commit() é automático
                    return True, "Dados atualizados com sucesso!"

        except IntegrityError as e:
            # Erro se o username ou email já estiverem em uso por *outro* usuário
            if 'users_username_key' in str(e):
                return False, "Esse nome de usuário já está em uso."
            if 'users_email_key' in str(e):
                return False, "Esse email já está em uso."
            return False, "Erro de integridade."
        except ValueError:
             return False, "Formato de data inválido. Use DD/MM/YYYY."
        except Exception as e:
            print(f"[ERRO] update_user_details: {e}")
            return False, f"Erro inesperado: {e}"
            