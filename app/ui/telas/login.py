from kivy.uix.screenmanager import Screen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from app.core.auth import Auth  # <-- Importa o "cérebro"


class LoginScreen(Screen):
    dialog = None

    def do_login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()

        # 1. Validação de tela (campos vazios)
        if not username or not password:
            self.show_popup("Erro", "Por favor, preencha todos os campos.")
            return

        # 2. Instancia o sistema de autenticação
        auth_system = Auth(self.manager.app.db)

        # 3. Chama o método de login (que agora retorna 4 valores)
        success, message, user_type, user_id = auth_system.login(username, password)

        if success:
            # SUCESSO! Armazena as informações do utilizador na app
            self.manager.app.logged_user_id = user_id
            self.manager.app.logged_user_type = user_type

            # Limpa os campos de texto por segurança
            self.ids.username.text = ""
            self.ids.password.text = ""

            # Decide para onde enviar o utilizador
            # (Pode ter lógicas diferentes para Paciente ou Psicólogo no futuro)
            if user_type == "Paciente":
                self.manager.current = "home"  # Envia para a 'home' do paciente
            elif user_type == "Psicólogo":
                self.manager.current = "home_psicologo"  # Ex: Envia para um dashboard diferente
            else:
                # Segurança: caso 'user_type' venha nulo
                self.manager.current = "main"

        else:
            # ERRO! Mostra a mensagem de falha (ex: "Utilizador ou senha inválidos.")
            self.show_popup("Erro de Login", message)

    def show_popup(self, title, message):
        """Função genérica para mostrar um pop-up de diálogo MD."""
        if self.dialog:
            self.dialog.dismiss()

        close_button = MDFlatButton(
            text="OK",
            on_release=self.close_dialog
        )
        self.dialog = MDDialog(
            title=title,
            text=message,
            buttons=[close_button]
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()