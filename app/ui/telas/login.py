from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivymd.uix.dialog import (
    MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivy.clock import Clock
from app.core.auth import Auth
import re

class LoginScreen(Screen):
    dialog = None
    spinner = None

    def do_login(self):
        email = self.ids.email_input.text.strip()
        password = self.ids.password.text.strip()

        if not email or not password:
            self.show_popup("Erro", "Por favor, preencha todos os campos.")
            return
        
        if not self.is_email_valido(email):
            self.ids.email_input.error = True # Fica vermelho no MDTextField
            self.show_popup("Formato de e-mail inválido!")
            return

        self.show_loading("Validando credenciais...")

        # Simula tempo de autenticação (use threads na prática)
        Clock.schedule_once(lambda dt: self._process_login(email, password), 1.5)

    def is_email_valido(self, email):
        padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if re.match(padrao, email):
            return True
        return False
    
    def _process_login(self, email, password):
        auth_system = Auth(self.manager.app.db)
        success, message, user_type, user_id, username = auth_system.login(email, password)

        self.hide_loading()

        if success:
            self.manager.app.logged_user_id = user_id
            self.manager.app.logged_user_type = user_type
            self.manager.app.logged_user_name = username
            
            self.ids.email_input.text = ""
            self.ids.password.text = ""

            if user_type == "Paciente":
                self.manager.current = "home"
            elif user_type == "Psicólogo":
                self.manager.current = "home_psicologo"
            else:
                self.manager.current = "main"
        else:
            self.show_popup("Erro de Login", message)

    # --- POPUP PADRÃO ---
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
            auto_dismiss=False,
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    # --- LOADING ---
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
