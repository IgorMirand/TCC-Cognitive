import re
from app.core.auth import Auth
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalInputDatePicker
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText

class RegisterScreen(Screen):
    """
    Tela de Registro refatorada para melhor gerenciamento de estado e UX.
    """
    spinner = None
    dialog = None
    menu_tipo = None

    def on_enter(self):
        """Chamado toda vez que a tela é exibida."""
        # Garante que a UI esteja construída antes de tentar manipular IDs
        Clock.schedule_once(self._init_ui_components, 0)
    
    def _init_ui_components(self, dt):
        """Inicializa menus e limpa o formulário."""
        self.create_menu_instance() # Apenas CRIA a instância, não abre
        self.clear_form()           # Reseta os campos visuais

    def clear_form(self):
        """Reseta o formulário para o estado inicial."""
        try:
            ids = self.ids
            
            # Verifica se os IDs existem antes de tentar acessar
            if not ids:
                return

            ids.username.text = ""
            ids.email_input.text = ""
            ids.email_input.error = False
            
            ids.password.text = ""
            ids.password.password = True
            
            # --- A CORREÇÃO ESTÁ AQUI ---
            # Tenta acessar o ícone de forma segura
            # Se a referência morreu, o bloco except abaixo vai capturar
            if hasattr(ids, 'password_icon'):
                ids.password_icon.icon = "eye-off"
            
            ids.data_nacimento.text = ""
            
            # Reset do Tipo de Usuário e Código
            ids.tipo_usuario.text = ""
            ids.codigo_acesso.text = ""
            ids.codigo_acesso.disabled = True
            
        except (AttributeError, ReferenceError):
            # ReferenceError: Captura o erro "weakly-referenced object no longer exists"
            # AttributeError: Captura caso o ID nem exista ainda
            pass

    def toggle_password_visibility(self):
        field = self.ids.password
        
        field.password = not field.password
        

    # --- Lógica do Menu Dropdown ---
    def create_menu_instance(self):
        """Cria a instância do menu."""
        if not self.menu_tipo:
            menu_items = [
                {
                    "text": "Paciente",
                    "on_release": lambda x="Paciente": self.set_tipo_usuario(x),
                },
                {
                    "text": "Psicólogo",
                    "on_release": lambda x="Psicólogo": self.set_tipo_usuario(x),
                },
            ]
            self.menu_tipo = MDDropdownMenu(
                caller=self.ids.tipo_usuario, # Garante que ele sabe quem chamou
                items=menu_items,
                position="bottom", # Força aparecer embaixo
                width_mult=4,
                max_height="200dp", # Limita altura para não bugar a tela
            )

    def open_menu_tipo(self):
        """Chamado pelo KV quando o campo recebe foco."""
        if not self.menu_tipo:
            self.create_menu_instance()
        self.menu_tipo.open()

    def set_tipo_usuario(self, tipo):
        """Define o valor e mostra/esconde o campo extra."""
        self.menu_tipo.dismiss()
        self.ids.tipo_usuario.text = tipo
        self.ids.tipo_usuario.focus = False 

        # Lógica simplificada: apenas mexemos no 'disabled' do campo.
        # O Container no KV observará essa mudança e ajustará a altura.
        campo_codigo = self.ids.codigo_acesso
        
        if tipo == "Psicólogo":
            campo_codigo.disabled = False
        else:
            campo_codigo.disabled = True
            campo_codigo.text = ""

    # --- Validação e Registro ---
    def do_register(self):
        # Coleta de dados
        username = self.ids.username.text.strip()
        password = self.ids.password.text.strip()
        email = self.ids.email_input.text.lower().strip()
        nascimento = self.ids.data_nacimento.text.strip()
        tipo = self.ids.tipo_usuario.text.strip()
        codigo = self.ids.codigo_acesso.text.strip()

        # Validações
        required_fields = [username, password, email, nascimento, tipo]
        if not all(required_fields):
            self.show_popup("Atenção", "Preencha todos os campos obrigatórios.")
            return

        if not self.is_email_valido(email):
            self.ids.email_input.error = True
            self.show_popup("Erro", "E-mail inválido.")
            return
            
        # Validação extra: Se escolheu Terapeuta, OBRIGATORIAMENTE precisa de código
        if tipo == "Psicólogo" and not codigo:
            self.show_popup("Atenção", "Terapeutas precisam de um Código de Acesso Mestre para se cadastrar.")
            return

        self.ids.email_input.error = False
        self.show_loading("Conectando ao servidor...")

        # Chama a função real em uma thread (simulada pelo Clock por enquanto)
        Clock.schedule_once(lambda dt: self._process_register_real(username, password, email, nascimento, codigo), 0.5)

    def _process_register_real(self, username, password, email, nascimento, codigo):
        app = MDApp.get_running_app()
        
        # Instancia o sistema de Auth passando o banco real
        auth_system = Auth(app.db)

        # Tenta registrar
        success, msg = auth_system.register(
            username=username,
            password=password,
            email=email,
            data_nascimento=nascimento, # Passa "DD/MM/YYYY"
            codigo=codigo # Passa "" ou o código digitado
        )

        self.hide_loading()

        if success:
            self.show_popup("Sucesso!", msg, action=lambda *x: self._go_to_login())
        else:
            self.show_popup("Erro no Registro", msg)

    def _go_to_login(self):
        self.dialog.dismiss()
        self.manager.current = "main" # Ou sua tela de login

    # --- Date Picker ---
    def show_modal_date_picker(self):
        # Evita abrir o calendário se o campo já tiver foco vindo de outro lugar
        # Mas garante que abra se for clicado
        if not hasattr(self, 'date_dialog'):
            self.date_dialog = MDModalInputDatePicker()
            self.date_dialog.bind(on_ok=self.on_date_selected, on_cancel=self.on_date_cancel)
        self.date_dialog.open()

    def on_date_selected(self, instance_date_picker):
        instance_date_picker.dismiss()
        selected = instance_date_picker.get_date()[0]
        if selected:
            self.ids.data_nacimento.text = selected.strftime("%d/%m/%Y")
        self.ids.data_nacimento.focus = False # Remove foco para permitir reabertura

    def on_date_cancel(self, instance_date_picker):
        instance_date_picker.dismiss()
        self.ids.data_nacimento.focus = False

    # --- Utilitários ---
    def is_email_valido(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def show_popup(self, title, message, action=None):
        if self.dialog:
            self.dialog.dismiss()
        
        btn_action = action if action else self.close_dialog
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=btn_action,
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