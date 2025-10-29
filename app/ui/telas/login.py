# app/ui/telas/login.py (Corrigido para KivyMD 2.0.0)

from kivy.uix.screenmanager import Screen
from app.core.auth import Auth

# (Importações necessárias para o MDDialog)
from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogSupportingText

class LoginScreen(Screen):
    dialog = None

    def do_login(self):
        # (O seu código de login está perfeito, não mude)
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()

        if not username or not password:
            self.show_popup("Erro", "Por favor, preencha todos os campos.")
            return

        auth_system = Auth(self.manager.app.db)
        success, message, user_type, user_id = auth_system.login(username, password)

        if success:
            self.manager.app.logged_user_id = user_id
            self.manager.app.logged_user_type = user_type
            
            self.ids.username.text = ""
            self.ids.password.text = ""

            if user_type == "Paciente":
                self.manager.current = "home"
            elif user_type == "Psicólogo":
                self.manager.current = "home_psicologo"
            else:
                self.manager.current = "main"
        else:
            self.show_popup("Erro de Login", message)

    
    # --- (A CORREÇÃO ESTÁ AQUI) ---
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