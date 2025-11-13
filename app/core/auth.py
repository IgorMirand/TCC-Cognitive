class Auth:
    def __init__(self, db):
        """
        Inicializa a classe Auth com uma instância do Database.
        :param db: Instância da classe Database
        """
        self.db = db

    # --- (1) ALTERAÇÃO AQUI (novos argumentos) ---
    def register(self, username, password, email, idade, codigo):
        """
        Gerencia toda a lógica de registro para qualquer tipo de usuário.
        Retorna uma tupla: (bool_sucesso, str_mensagem)
        """
        try:
            # --- CENÁRIO 1: Paciente sem código (cadastro simples) ---
            if not codigo:
                # (Passe email e idade para a função do DB)
                success, msg, user_id = self.db.register_user(username, password, "Paciente", email, idade)
                if success:
                    return True, "Conta de paciente criada. Você pode se vincular a um psicólogo no seu perfil."
                else:
                    return False, msg  # Ex: "Usuário já existe."

            # Se um código foi fornecido, checa os outros cenários:

            # --- CENÁRIO 2: É um código-mestre de Psicólogo? ---
            codigo_master_id = self.db.validar_codigo_master(codigo)
            if codigo_master_id:
                # É um psicólogo. Tenta registrar.
                success, msg, user_id = self.db.register_user(username, password, "Psicólogo", email, idade)
                if success:
                    # Se o registro deu certo, marca o código como usado
                    self.db.marcar_codigo_master_usado(codigo_master_id, user_id)
                    return True, "Conta de Psicólogo criada com sucesso!"
                else:
                    return False, msg  # Ex: "Usuário já existe"

            # --- CENÁRIO 3: É um código de Paciente (para vínculo)? ---
            psicologo_id = self.db.validar_codigo_paciente(codigo)
            if psicologo_id:
                # É um paciente. Tenta registrar.
                success, msg, paciente_id = self.db.register_user(username, password, "Paciente", email, idade)
                if not success:
                    return False, msg  # Ex: "Usuário já existe"
                
                # Se o registro deu certo, faz o vínculo
                self.db.vincular_paciente_psicologo(paciente_id, psicologo_id)
                self.db.marcar_codigo_paciente_usado(codigo, paciente_id)

                return True, "Conta de paciente criada e vinculada ao seu psicólogo!"

            # --- CENÁRIO 4: O código foi fornecido, mas não é válido ---
            return False, "Código de Acesso inválido."

        except Exception as e:
            print(f"[ERRO] Auth.register: {e}")
            return False, "Ocorreu um erro inesperado durante o registro."

    def login(self, name, password):
        """
        Gerencia a lógica de login.
        Retorna: (bool_sucesso, str_mensagem, str_user_type, int_user_id)
        """
        success, msg, user_type, user_id, username = self.db.verify_user(name, password)

        if success:
            return True, msg, user_type, user_id, username
        else:
            return False, msg, None, None
        