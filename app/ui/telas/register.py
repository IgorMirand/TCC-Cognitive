from kivy.uix.screenmanager import Screen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from app.core.auth import Auth

class RegisterScreen(Screen):
    dialog = None

    def do_register(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()
        codigo = self.ids.codigo_acesso.text.strip()

        # 1. Validação de tela (campos vazios)
        if not username or not password:
            self.show_popup("Erro", "Username e Senha são obrigatórios.")
            return

        # 2. Delega a lógica para a classe Auth
        #    'self.manager.app.db' é a instância do banco de dados
        #    que você criou no main.py
        auth_system = Auth(self.manager.app.db)

        # 3. Chama o método único de registro
        success, message = auth_system.register(username, password, codigo)

        # 4. Apenas mostra o resultado (sucesso ou erro)
        if success:
            self.show_popup("Sucesso", message)
            self.manager.current = "login"  # Manda para o login
        else:
            self.show_popup("Erro", message)

    # (Funções show_popup e close_dialog permanecem as mesmas)
    def show_popup(self, title, message):
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

class RegisterScreen1(Screen):
    dialog = None
    def next(self):
        

        try:
            nome = self.ids.nome.text.strip()
            idade = int(self.ids.idade.text.strip())
            email = self.ids.email.text.strip()
            # 1. Validação de tela (campos vazios)
            if not nome or not idade or not email:
                self.show_popup("Erro", "Nome, Idade e Email são obrigatórios.")
            else:
                self.manager.current = "register"
        except ValueError:
                self.show_popup("Erro", "Idade")

    def show_popup(self, title, message):
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
