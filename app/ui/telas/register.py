from kivy.uix.screenmanager import Screen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from app.core.auth import Auth
from kivy.uix.widget import Widget
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogSupportingText
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivy.clock import Clock

class RegisterScreen(Screen):
    spinner = None
    dialog = None

    def do_register(self):
        # 1. Obter todos os dados dos campos
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()
        email = self.ids.email_input.text.strip()     # <-- NOVO
        idade_raw = self.ids.idade_input.text.strip() # <-- NOVO
        codigo = self.ids.codigo_acesso.text.strip()

        # 2. Validar campos obrigatórios
        if not username or not password or not email or not idade_raw:
            self.show_popup("Erro", "Todos os campos (exceto o código) são obrigatórios.")
            return
            
        if "@" not in email or "." not in email:
            self.show_popup("Erro", "Por favor, insira um email válido.")
            return
            
        try:
            idade = int(idade_raw) # Tenta converter a idade para número
            if idade < 13: # Exemplo de restrição de idade
                 self.show_popup("Erro", "Você deve ter pelo menos 13 anos.")
                 return
        except ValueError:
            self.show_popup("Erro", "Por favor, insira uma idade válida (apenas números).")
            return
        
        self.show_loading("Validando credenciais...")
        # Simula tempo de autenticação (use threads na prática)
        Clock.schedule_once(lambda dt: self._process_register(username, password, email, idade, codigo))

        
    def _process_register(self, username, password, email, idade, codigo):
        auth_system = Auth(self.manager.app.db)
        success, msg = auth_system.register(username, password, email, idade, codigo)
        self.hide_loading()
        try:
            if success:
                self.show_popup("Sucesso", msg)
                self.manager.current = "login" # Envia para login após sucesso
            else:
                self.show_popup("Erro", msg)

        except Exception as e:
            print(f"Erro ao registrar: {e}")
            self.show_popup("Erro de Sistema", "Não foi possível completar o registro.")


    def on_pre_enter(self):
        """Cria o menu de tipo de usuário quando a tela abre"""
        Clock.schedule_once(self.create_menu, 0)

    def create_menu(self, *args):
        """Cria o menu dropdown com as opções"""
        menu_items = [
            {"text": "Usuário", "on_release": lambda x="Usuário": self.set_tipo_usuario(x)},
            {"text": "Terapeuta", "on_release": lambda x="Terapeuta": self.set_tipo_usuario(x)},
        ]

        self.menu_tipo = MDDropdownMenu(
            caller=self.ids.tipo_usuario,
            items=menu_items,
            width_mult=3,
        )

    def set_tipo_usuario(self, tipo):
        """Define o texto do campo e mostra/esconde o código"""
        self.menu_tipo.dismiss()
        self.ids.tipo_usuario.set = tipo

        campo = self.ids.codigo_acesso

        if tipo == "Terapeuta":
            # Se for terapeuta, mostra o campo
            campo.opacity = 1
            campo.disabled = False
        else:
            # Se for usuário, esconde
            campo.opacity = 0
            campo.disabled = True

    # (Funções show_popup e close_dialog permanecem as mesmas)
    def show_popup(self, title, message):
        """Função genérica para mostrar um pop-up (Sintaxe KivyMD 2.0.0)"""
        if self.dialog:
            self.dialog.dismiss()
        
        # 4. Crie o diálogo
        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text=title,
            ),
            MDDialogSupportingText(
                text=message,
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=self.close_dialog,
                ),
                spacing="8dp",
            ),
            auto_dismiss=False,
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def show_loading(self, message="Carregando..."):
        """Mostra o indicador de carregamento"""
        if self.spinner:
            return  # já está mostrando

        self.spinner = MDCircularProgressIndicator(size_hint=(None, None), size=("48dp", "48dp"))
        self.add_widget(self.spinner)
        self.spinner.pos_hint = {"center_x": 0.5, "center_y": 0.5}

    def hide_loading(self, *args):
        """Remove o indicador"""
        if self.spinner:
            self.remove_widget(self.spinner)
            self.spinner = None
