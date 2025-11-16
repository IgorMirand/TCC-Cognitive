from kivymd.uix.screen import Screen
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText, MDListItemSupportingText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer
)
from kivymd.uix.button import MDButton, MDButtonText
from kivy.uix.widget import Widget
from datetime import date

class BaseScreen(Screen):

    def get_app(self):
        """Retorna a instância principal do App."""
        return MDApp.get_running_app()

    def get_db(self):
        """Atalho para acessar o banco de dados."""
        return self.get_app().db
    
    def get_user_id(self):
        """Atalho para pegar o ID do usuário logado."""
        return self.get_app().logged_user_id

    def get_user_name(self):
        """Atalho para pegar o Nome do usuário logado."""
        return getattr(self.get_app(), 'logged_user_name', 'Paciente')
    
    def get_user_type(self):
        """Retorna 'Psicólogo' ou 'Paciente'."""
        return getattr(self.get_app(), 'logged_user_type', 'Paciente')
    


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

class ContaScreen(BaseScreen):
    def on_enter(self, *args):
        self.carregar_dados()
        self.montar_menu()
    
    def _calcular_idade(self, data_nasc_obj):
        """Helper para calcular a idade a partir de um objeto date."""
        if not data_nasc_obj:
            return "?"
        
        hoje = date.today()
        # Cálculo preciso que considera se o aniversário já passou no ano
        idade = hoje.year - data_nasc_obj.year - ((hoje.month, hoje.day) < (data_nasc_obj.month, data_nasc_obj.day))
        return str(idade)

    def carregar_dados(self):
        # Pega o nome e tipo (como antes)
        self.ids.lbl_nome.text = self.get_user_name()
        tipo = self.get_user_type()
        self.ids.lbl_email.text = f"Perfil: {tipo}"

        # Agora, busca detalhes (incluindo data de nasc.) para a idade
        try:
            db = self.get_db()
            user_id = self.get_user_id()
            # A função get_user_details retorna (username, email, data_obj)
            dados = db.get_user_details(user_id) 
            
            if dados:
                data_nasc_obj = dados[2] # O terceiro item é a data de nascimento
                idade = self._calcular_idade(data_nasc_obj)
                self.ids.lbl_idade.text = f"{idade} anos"
            else:
                # Falha ao buscar dados (raro, mas possível)
                self.ids.lbl_idade.text = "Idade: N/D"

        except Exception as e:
            print(f"Erro ao buscar detalhes para idade: {e}")
            self.ids.lbl_idade.text = "Idade: -"

    def montar_menu(self):
        """Cria os itens do menu dinamicamente baseado no tipo de usuário."""
        menu_list = self.ids.menu_list
        menu_list.clear_widgets() # Limpa itens antigos
        
        tipo = self.get_user_type()

        # --- ITENS COMUNS ---
        self.adicionar_item(
            menu_list, 
            "Meus Dados", 
            "Editar informações pessoais", 
            "account-cog-outline",
            lambda x: setattr(self.manager, 'current', 'editar_dados')
        )

        # --- ITENS ESPECÍFICOS ---
        if tipo == "Paciente":
            self.adicionar_item(
                menu_list, 
                "Meu Psicólogo", 
                "Ver profissional vinculado", 
                "doctor", 
                lambda x: print("Ver psicólogo")
            )
        
        elif tipo == "Psicólogo":
            self.adicionar_item(
                menu_list, 
                "Exportar Relatórios", 
                "Baixar dados dos pacientes", 
                "file-document-outline", 
                lambda x: print("Exportar PDF")
            )
            self.adicionar_item(
                menu_list, 
                "Configurar Atividades", 
                "Gerenciar templates globais", 
                "playlist-edit", 
                lambda x: setattr(self.manager, 'current', 'lista_atividade')
            )

        # --- ITEM DE LOGOUT (SEMPRE O ÚLTIMO) ---
        self.adicionar_item(
            menu_list, 
            "Sair do App", 
            "", 
            "logout", 
            self.fazer_logout,
            is_logout=True
        )

    def adicionar_item(self, container, titulo, subtitulo, icone, acao, is_logout=False):
        """Helper para criar MDListItem do KivyMD 2.0"""
        
        cor_icone = "#F44336" if is_logout else "#92C7A3"
        cor_texto = "Error" if is_logout else "Primary"
        
        # --- CORREÇÃO AQUI: Removemos style="elevated" ---
        item = MDListItem(
            MDListItemLeadingIcon(
                icon=icone,
                theme_icon_color="Custom",
                icon_color=cor_icone
            ),
            MDListItemHeadlineText(
                text=titulo,
                theme_text_color=cor_texto
            ),
            
            theme_bg_color="Custom",
            md_bg_color=[1, 1, 1, 1], # Fundo Branco
            radius=[16],              # Bordas arredondadas
            pos_hint={"center_x": .5},
            on_release=acao
        )
        
        if subtitulo:
            item.add_widget(MDListItemSupportingText(text=subtitulo))
            
        container.add_widget(item)

    def fazer_logout(self, *args):
        app = self.get_app()
        app.logged_user_id = None
        app.logged_user_name = None
        app.logged_user_type = None
        app.root.current = "main"

class EditarDadosScreen(BaseScreen):
    
    def on_enter(self, *args):
        """Chamado sempre que a tela é exibida. Carrega os dados."""
        self.carregar_dados_atuais()

    def carregar_dados_atuais(self):
        """Busca os dados do DB e preenche os campos."""
        db = self.get_db()
        user_id = self.get_user_id()
        
        dados = db.get_user_details(user_id)
        
        if dados:
            username, email, data_obj = dados
            self.ids.field_username.text = username
            self.ids.field_email.text = email
            # Formata o objeto 'date' do banco para string DD/MM/YYYY
            self.ids.field_nasc.text = data_obj.strftime("%d/%m/%Y")
        else:
            self.show_popup("Erro", "Não foi possível carregar seus dados.")

    def salvar_dados(self):
        """Pega os dados dos campos e envia para o DB."""
        db = self.get_db()
        user_id = self.get_user_id()
        
        # Pega os valores dos campos de texto
        username = self.ids.field_username.text.strip()
        email = self.ids.field_email.text.strip()
        nascimento = self.ids.field_nasc.text.strip()
        
        if not (username and email and nascimento):
            self.show_popup("Erro", "Todos os campos são obrigatórios.")
            return
            
        # Chama a nova função do DB
        success, message = db.update_user_details(
            user_id, 
            username, 
            email, 
            nascimento
        )
        
        if success:
            # IMPORTANTE: Atualiza o nome de usuário na sessão da app
            app = self.get_app()
            app.logged_user_name = username
            
            self.show_popup("Sucesso!", message)
            self.manager.current = "conta" # Volta para a tela de conta
        else:
            self.show_popup("Erro ao Salvar", message)
