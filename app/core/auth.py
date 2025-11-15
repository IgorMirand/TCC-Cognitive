class Auth:
    def __init__(self, db):
        self.db = db

    # --- (1) ALTERAÇÃO AQUI (novos argumentos) ---
    def register(self, username, password, email, data_nascimento, codigo):
        """
        Gerencia o registro. O parâmetro 'codigo' pode ser vazio ("").
        """
        try:
            # --- CENÁRIO 1: Paciente sem código (cadastro simples) ---
            if not codigo:
                # Passa data_nascimento
                success, msg, user_id = self.db.register_user(username, password, "Paciente", email, data_nascimento)
                if success:
                    return True, "Conta criada! Faça login para continuar."
                else:
                    return False, msg

            # --- CENÁRIO 2: É um código-mestre de Psicólogo? ---
            codigo_master_id = self.db.validar_codigo_master(codigo)
            if codigo_master_id:
                success, msg, user_id = self.db.register_user(username, password, "Psicólogo", email, data_nascimento)
                if success:
                    self.db.marcar_codigo_master_usado(codigo_master_id, user_id)
                    return True, "Conta de Psicólogo criada com sucesso!"
                else:
                    return False, msg


        except Exception as e:
            print(f"[ERRO] Auth.register: {e}")
            return False, "Erro técnico durante o registro."

    def login(self, name, password):
        try:
            # 1. Capturamos o retorno bruto do banco em uma variável primeiro
            resultado_db = self.db.verify_user(name, password)

            # 2. Programação Defensiva: Verificamos o tamanho da resposta
            if len(resultado_db) == 5:
                # Cenário ideal: Banco retornou tudo
                success, msg, user_type, user_id, username = resultado_db
            
            elif len(resultado_db) == 4:
                # Cenário do erro atual: Banco esqueceu o username
                success, msg, user_type, user_id = resultado_db
                # Fallback: Usamos o email (name) como username temporário ou uma string vazia
                username = name.split('@')[0] if '@' in name else name
            
            else:
                # Cenário desconhecido
                print(f"[CRITICAL] Retorno do banco inesperado: {resultado_db}")
                return False, "Erro interno: Formato de dados inválido.", None, None, None

            # 3. Retornamos sempre 5 valores para o front-end (login.py)
            return success, msg, user_type, user_id, username

        except ValueError as e:
            # Captura erro específico de desempacotamento se algo muito estranho ocorrer
            print(f"[ERRO] Falha ao desempacotar login: {e}")
            return False, "Erro de comunicação com o banco de dados.", None, None, None
            
        except Exception as e:
            # Captura qualquer outro erro genérico para o app não fechar
            print(f"[ERRO] Erro desconhecido no login: {e}")
            return False, "Ocorreu um erro inesperado ao tentar logar.", None, None, None