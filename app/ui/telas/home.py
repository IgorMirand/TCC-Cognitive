from kivymd.uix.screen import Screen

# (Importações necessárias para o Pop-up KivyMD 2.0.0)
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton,MDButtonText
from kivy.uix.widget import Widget


class HomeScreen(Screen):
    """
    Tela 'Home' do Paciente.
    """
    dialog = None

    def vincula(self):
        """
        Chamado pelo botão "Vincular" no .kv.
        Tenta vincular este paciente (logado) usando o código do text field.
        """
        # Pega o ID do paciente logado
        paciente_id = self.manager.app.logged_user_id
        # Pega o código digitado
        codigo = self.ids.vincula_input.text.strip()

        # Validação simples
        if not paciente_id:
            self.show_popup("Erro", "Não foi possível identificar o seu login. Tente novamente.")
            return
        if not codigo:
            self.show_popup("Erro", "Por favor, digite o código de convite.")
            return

        # Pega a instância do banco de dados
        db = self.manager.app.db
        
        # Chama a nova função da base de dados
        success, msg = db.vincular_paciente_por_codigo(paciente_id, codigo)

        if success:
            self.show_popup("Sucesso!", msg)
            self.ids.vincula_input.text = "" # Limpa o campo
            # Opcional: Esconder o card de vincular
            # self.ids.vincula_card.height = 0
            # self.ids.vincula_card.opacity = 0
        else:
            self.show_popup("Erro", msg)


    def show_email_dialog(self):
        # Cria o campo de texto e o guarda como atributo
        self.email_input = MDTextField(
            MDTextFieldLeadingIcon(icon="email-outline"),
            MDTextFieldHintText(text="Digite o email do paciente"),
        )

        # Cria o diálogo
        self.email_dialog = MDDialog(
            MDDialogHeadlineText(text="Enviar convite"),
            MDDialogContentContainer(self.email_input),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancelar"),
                    style="text",
                    on_release=self.close_dialog
                ),
                MDButton(
                    MDButtonText(text="Enviar"),
                    style="text",
                    on_release=self.iniciar_envio_email
                ),
                spacing="8dp",
            ),
        )
        self.email_dialog.open()

    # --- Funções de Pop-up (KivyMD 2.0.0) ---
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
                spacing="8dp"
            ),
            auto_dismiss=False
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
