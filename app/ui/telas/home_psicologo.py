from kivymd.uix.screen import MDScreen
from kivy.metrics import dp
from kivy.clock import Clock
import threading
import os
import sendgrid

# (Importações corretas para o Pop-up KivyMD 2.0.0)
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer
)
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldLeadingIcon,
    MDTextFieldHintText,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.progressindicator.progressindicator import MDCircularProgressIndicator
from kivymd.uix.label import MDLabel
from sendgrid.helpers.mail import Mail, Email, To, Content


class PsychoHomeScreen(MDScreen):
    dialog = None # Para o pop-up de OK/Erro
    loading_dialog = None # Para o pop-up de "Enviando..."
    email_dialog = None # Para o pop-up que pede o email

    def on_enter(self, *args):
        """Chamado sempre que a tela é exibida."""
        self.load_user_data()

    def load_user_data(self):
        """Carrega o ID do psicólogo logado."""
        try:
            user_id = self.manager.app.logged_user_id
            self.ids.id_label.text = f"ID : {user_id}" 
        except Exception as e:
            print(f"Erro ao carregar dados do psicólogo: {e}")
            self.ids.id_label.text = "ID : Erro"

    def navigate_to(self, screen_name):
        """Navega para outras telas (ex: lista de pacientes)."""
        # (Adicione a navegação aqui)
        if screen_name == "consulta_anotacao":
            self.manager.current = "consulta_anotacao"
        else:
            print(f"Navegando para: {screen_name}")

    # --- (1) LÓGICA DO POP-UP DE CONVITE (O CARD) ---
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


    def iniciar_envio_email(self, *args):
        paciente_email = self.email_input.text.strip()
        if not paciente_email or "@" not in paciente_email:
            self.show_ok_dialog("Erro", "Por favor, insira um email válido.")
            return

        self.show_loading_dialog("Enviando convite...")

        threading.Thread(target=self._send_invite_backend, args=(paciente_email,)).start()


    def _send_invite_backend(self, paciente_email):
        try:
            psicologo_id = self.manager.app.logged_user_id
            db = self.manager.app.db
            codigo = db.gerar_codigo_paciente(psicologo_id)

            url = "https://SEU_BACKEND_URL/send-invite"
            data = {
                "email": paciente_email,
                "codigo": codigo,
                "psicologo": "Dr. João Silva"
            }
            response = requests.post(url, json=data)

            if response.status_code == 200:
                resultado = ("Sucesso", f"Convite enviado para {paciente_email}!")
            else:
                resultado = ("Erro", f"Falha no envio: {response.json().get('message')}")
        except Exception as e:
            resultado = ("Erro", f"Erro inesperado: {e}")

        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._envio_email_callback(resultado))

    # --- (2) LÓGICA DE EMAIL EM SEGUNDO PLANO (THREAD) ---
    def _thread_enviar_email_worker(self, paciente_email, psicologo_id):
        """
        Envia e-mail de convite via SendGrid (para um único paciente).
        Roda em thread separada.
        """
        try:
            db = self.manager.app.db

            # Gera o código de convite
            novo_codigo = db.gerar_codigo_paciente(psicologo_id)
            if not novo_codigo:
                raise Exception("Falha ao gerar código no banco de dados.")

            # Configura SendGrid
            sg_api_key = os.environ.get("SENDGRID_API_KEY")
            remetente = os.environ.get("EMAIL_SENDER")
            if not sg_api_key or not remetente:
                raise Exception("Configuração ausente: SENDGRID_API_KEY ou EMAIL_SENDER.")

            sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)

            # Corpo do e-mail
            assunto = "Convite para a plataforma Cognitive"
            corpo_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background:#f7f9fc; padding:20px;">
                <div style="max-width:600px;margin:auto;background:white;border-radius:8px;padding:20px;">
                    <h2 style="color:#2563EB;text-align:center;">Convite Cognitive</h2>
                    <p>Olá!</p>
                    <p>O seu psicólogo convidou você para se juntar à plataforma <b>Cognitive</b>.</p>
                    <p>Use este código de acesso ao criar sua conta:</p>
                    <div style="font-size:28px;font-weight:bold;color:#2563EB;text-align:center;margin:16px 0;">
                        {novo_codigo}
                    </div>
                    <a href="https://cognitive.app/register"
                    style="display:inline-block;background:#2563EB;color:white;
                            padding:10px 20px;border-radius:6px;text-decoration:none;">
                    Criar conta agora
                    </a>
                    <p style="margin-top:20px;">Obrigado por usar o Cognitive 💙</p>
                </div>
            </body>
            </html>
            """

            # Monta o e-mail
            mensagem = Mail(
                from_email=Email(remetente, "Cognitive App"),
                to_emails=To(paciente_email),
                subject=assunto,
                html_content=Content("text/html", corpo_html)
            )

            # Envia via SendGrid
            resposta = sg.client.mail.send.post(request_body=mensagem.get())
            print(f"✅ E-mail enviado! Status: {resposta.status_code}")

            if resposta.status_code not in [200, 202]:
                raise Exception(f"Erro SendGrid: {resposta.status_code}")

            resultado = ("Sucesso", f"Convite enviado com sucesso para {paciente_email}!")

        except Exception as e:
            print(f"[ERRO NO ENVIO DE EMAIL]: {e}")
            resultado = ("Erro", f"Falha ao enviar e-mail: {e}")

        # Atualiza a interface na thread principal
        Clock.schedule_once(lambda dt: self._envio_email_callback(resultado))


    def _envio_email_callback(self, resultado):
        """(Esta função corre na MAIN THREAD)"""
        titulo, mensagem = resultado
        self.dismiss_loading_dialog()
        self.show_ok_dialog(titulo, mensagem)

    # --- (3) FUNÇÕES DE POP-UP (KivyMD 2.0.0 Corretas) ---
    def show_loading_dialog(self, text="Enviando..."):
        if self.loading_dialog:
            self.loading_dialog.dismiss()
        
        spinner = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=("46dp", "46dp"),
            color="primary",
            pos_hint={'center_x': .5},
        )

        content = MDDialogContentContainer(orientation="vertical", spacing="10dp")
        content.add_widget(spinner)
        content.add_widget(MDLabel(text=text, halign="center"))

        self.loading_dialog = MDDialog(content, auto_dismiss=False)
        self.loading_dialog.open()


    def show_ok_dialog(self, title, message): 
        if self.dialog: 
            self.dialog.dismiss() 
        ok_button = MDButton(text="OK", style="text", on_release=self.close_dialog) 
        button_container = MDDialogButtonContainer(spacing="8dp") 
        button_container.add_widget(ok_button) # <-- CORREÇÃO: Adiciona com add_widget 
        self.dialog = MDDialog( MDDialogHeadlineText(text=title), MDDialogSupportingText(text=message), [button_container], auto_dismiss=False, ) 
        self.dialog.open()


    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None


    def show_loading_dialog(self, text="Enviando..."):
        if self.loading_dialog:
            self.loading_dialog.dismiss()
        
        spinner_widget = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=("46dp", "46dp"),
            pos_hint={'center_x': .5},
        )
        
        content_container = MDDialogContentContainer(orientation="vertical")
        content_container.add_widget(spinner_widget) # <-- CORREÇÃO: Adiciona com add_widget

        self.loading_dialog = MDDialog(
            MDDialogHeadlineText(text=text),
            content_container, # Passa o container
            auto_dismiss=False,
        )
        self.loading_dialog.open()

    def dismiss_loading_dialog(self):
        if self.loading_dialog:
            self.loading_dialog.dismiss()
            self.loading_dialog = None

