import re
import requests
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.progressindicator import MDCircularProgressIndicator

# Importações necessárias para os ícones e campos novos
from kivymd.uix.textfield import MDTextFieldTrailingIcon
from kivymd.uix.button import MDIconButton

# Importe sua classe de autenticação aqui se não estiver no main
from app.core.auth import Auth

class LoginScreen(Screen):
    dialog = None
    spinner = None

    def toggle_password_visibility(self):
        """Alterna entre mostrar e esconder a senha."""
        field = self.ids.password
        
        field.password = not field.password

    def do_login(self):
        email = self.ids.email_input.text.lower().strip()
        password = self.ids.password.text.strip()

        # Validação básica
        if not email or not password:
            self.show_popup("Atenção", "Por favor, preencha email e senha.")
            return
        
        if not self.is_email_valido(email):
            self.ids.email_input.error = True
            self.show_popup("Erro", "O formato do e-mail está incorreto.")
            return
        
        # Remove estado de erro se estiver tudo ok
        self.ids.email_input.error = False
        
        self.show_loading("Autenticando...")

        # Simula delay de rede
        Clock.schedule_once(lambda dt: self._process_login(email, password), 1.5)

    def _process_login(self, email, password):
        app = MDApp.get_running_app()
        # Garanta que 'app.db' existe no seu main.py
        auth_system = Auth(app.db)
        
        success, message, user_type, user_id, username = auth_system.login(email, password)

        self.hide_loading()

        if success:
            app.logged_user_id = user_id
            app.logged_user_type = user_type
            app.logged_user_name = username
            
            self._clear_fields()

            # Roteamento
            if user_type == "Paciente":
                self.manager.current = "home"
            elif user_type == "Psicólogo": # Ajustei de Psicólogo para manter padrão
                self.manager.current = "home_psicologo"
            else:
                self.manager.current = "main"
        else:
            self.show_popup("Falha no Login", message)

    def _clear_fields(self):
        """Limpa os campos de forma segura, ignorando erros de memória."""
        try:
            # Verifica se os IDs ainda existem na memória
            if not self.ids:
                return

            self.ids.email_input.text = ""
            self.ids.password.text = ""
            self.ids.password.password = True
            
            # Tenta acessar o ícone. Se a referência morreu, o except pega.
            # Usamos getattr para segurança extra em vez de acesso direto se possível,
            # ou simplesmente envolvemos no bloco try.
            if hasattr(self.ids, 'password_icon'):
                self.ids.password_icon.icon = "eye-off"

        except (AttributeError, ReferenceError):
            # ReferenceError: O objeto (botão/campo) já foi limpo da memória
            # AttributeError: O ID não foi encontrado
            # Em ambos os casos, não precisamos fazer nada, pois a tela já foi trocada.
            pass

    def is_email_valido(self, email):
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(padrao, email) is not None

    # --- POPUPS E LOADING (Mantidos iguais ao Register) ---
    def show_popup(self, title, message):
        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=self.close_dialog,
                ),
                spacing="8dp",
            ),
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def show_loading(self, message="Carregando..."):
        if not self.spinner:
            self.spinner = MDCircularProgressIndicator(
                size_hint=(None, None), 
                size=("48dp", "48dp"),
                pos_hint={'center_x': .5, 'center_y': .5}
            )
            self.add_widget(self.spinner)

    def hide_loading(self, *args):
        if self.spinner:
            self.remove_widget(self.spinner)
            self.spinner = None