from kivymd.uix.screen import Screen
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText, MDListItemSupportingText

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

class ContaScreen(BaseScreen):
    def on_enter(self, *args):
        self.carregar_dados()
        self.montar_menu()

    def carregar_dados(self):
        # Pega dados da BaseScreen
        self.ids.lbl_nome.text = self.get_user_name()
        
        tipo = self.get_user_type()
        self.ids.lbl_email.text = f"Perfil: {tipo}"

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
            lambda x: print("Ir para editar dados")
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