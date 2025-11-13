from kivymd.uix.screen import Screen

# (Importações necessárias para o Pop-up KivyMD 2.0.0)
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
from kivymd.uix.button import MDButton,MDButtonText
from kivymd.uix.label import MDLabel
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.icon_definitions import md_icons

class HomeScreen(Screen):

    dialog = None

    def on_enter(self, *args):
        """Chamado sempre que a tela é exibida."""
        self.load_user_data()

    def load_user_data(self):
        """Carrega o NOME e ID do psicólogo logado."""
        try:
            # Verifica se o ID e Nome estão disponíveis na App class
            if hasattr(self.manager.app, 'logged_user_name'):
                username = self.manager.app.logged_user_name
                self.ids.id_label.text = f"Ola, {username}"
            else:
                self.ids.id_label.text = "Bem-vindo(a), Paciente"
            
        except Exception as e:
            print(f"Erro ao carregar dados do Paciente: {e}")
            self.ids.id_label.text = "Bem-vindo"

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
            self.ids.vincula_card.height = 0
            self.ids.vincula_card.opacity = 0
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

class AgendamentoScreen(Screen):
    def on_enter(self):
        self.carregar_horarios()

    def carregar_horarios(self):
        container = self.ids.container_horarios
        container.clear_widgets()
        
        db = self.manager.app.db
        paciente_id = self.manager.app.logged_user_id
        
        # 1. Descobrir quem é o psicólogo desse paciente
        psicologo_id = db.get_psicologo_id_by_paciente(paciente_id) 
        
        if not psicologo_id:
            container.add_widget(MDLabel(text="Você ainda não tem psicólogo vinculado.", halign="center"))
            return

        # 2. Buscar horários livres desse psicólogo
        horarios = db.get_horarios_disponiveis(psicologo_id)
        
        if not horarios:
            container.add_widget(MDLabel(text="Sem horários disponíveis no momento.", halign="center"))
            return

        for ag_id, dt_obj in horarios:
            data_fmt = dt_obj.strftime("%d/%m - %H:%M") # Ex: 12/11 - 14:00
            
            # Card simples para cada horário
            card = MDCard(
                style="elevated",
                size_hint_y=None,
                height="80dp",
                padding="15dp",
                ripple_behavior=True,
                on_release=lambda x, i=ag_id, d=data_fmt: self.confirmar_agendamento(i, d)
            )
            
            layout = MDBoxLayout(orientation="horizontal")
            layout.add_widget(md_icons(icon="calendar-check", pos_hint={"center_y": .5}))
            layout.add_widget(MDLabel(text=data_fmt, font_style="Title", role="medium", pos_hint={"center_y": .5}, padding=[20,0,0,0]))
            
            card.add_widget(layout)
            container.add_widget(card)

    def confirmar_agendamento(self, agenda_id, data_texto):
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Confirmar Agendamento"),
            MDDialogSupportingText(text=f"Deseja marcar consulta para {data_texto}?"),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancelar"), on_release=lambda x: self.dialog.dismiss()),
                MDButton(MDButtonText(text="Confirmar"), on_release=lambda x: self.finalizar_agendamento(agenda_id))
            )
        )
        self.dialog.open()

    def finalizar_agendamento(self, agenda_id):
        db = self.manager.app.db
        paciente_id = self.manager.app.logged_user_id
        
        success, msg = db.agendar_consulta(agenda_id, paciente_id)
        
        self.dialog.dismiss()
        # Feedback visual simples (pode ser um dialog de sucesso)
        print(msg) 
        if success:
            self.manager.current = "home" # Volta pra home após agendar
