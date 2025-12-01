from kivymd.uix.screen import Screen
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemHeadlineText, MDListItemSupportingText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogContentContainer,
    MDDialogButtonContainer
)
from kivymd.uix.button import MDButton, MDButtonText
from kivy.uix.widget import Widget
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.boxlayout import MDBoxLayout
from datetime import datetime

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
    dialog = None
    
    def on_enter(self, *args):
        self.carregar_dados()
        self.montar_menu()
    
    def _calcular_idade(self, data_nasc_str):
        """
        Calcula idade aceitando formatos BR (DD/MM/AAAA) ou ISO (AAAA-MM-DD).
        """
        # Se a data for vazia, None ou string "None", retorna ?
        if not data_nasc_str or str(data_nasc_str).lower() == "none" or data_nasc_str == "":
            return "?"
        
        dt_nasc = None
        
        try:
            # Tentativa 1: Formato Brasileiro (O mais provável vindo do neon.py)
            dt_nasc = datetime.strptime(data_nasc_str, "%d/%m/%Y")
        except ValueError:
            try:
                # Tentativa 2: Formato ISO (Caso venha direto do banco sem converter)
                dt_nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d")
            except ValueError:
                return "?" # Formato desconhecido

        # Se conseguiu converter, calcula a idade
        if dt_nasc:
            hoje = datetime.today()
            idade = hoje.year - dt_nasc.year - ((hoje.month, hoje.day) < (dt_nasc.month, dt_nasc.day))
            return str(idade)
            
        return "?"

    def carregar_dados(self):
        # Pega o nome e tipo (cache local)
        self.ids.lbl_nome.text = self.get_user_name()
        tipo = self.get_user_type()
        self.ids.lbl_email.text = f"Perfil: {tipo}"

        # Busca detalhes na API
        try:
            db = self.get_db()
            user_id = self.get_user_id()
            
            # Retorna DICT: {'username': '...', 'data_nascimento': '01/01/2000', ...}
            dados = db.get_user_details(user_id) 
            
            if dados:
                # --- CORREÇÃO AQUI ---
                # Usamos .get('chave') em vez de índice [2]
                data_nasc_str = dados.get('data_nascimento') 
                
                idade = self._calcular_idade(data_nasc_str)
                self.ids.lbl_idade.text = f"{idade} anos"
            else:
                self.ids.lbl_idade.text = "Idade: N/D"

        except Exception as e:
            print(f"Erro ao buscar detalhes para idade: {e}")
            self.ids.lbl_idade.text = "Idade: -"

    def montar_menu(self):
        """Cria os itens do menu dinamicamente baseado no tipo de usuário."""
        menu_list = self.ids.menu_list
        menu_list.clear_widgets() 
        
        tipo = self.get_user_type()

        # Meus Dados
        self.adicionar_item(
            menu_list, 
            "Meus Dados", 
            "Editar informações pessoais", 
            "account-cog-outline",
            lambda x: setattr(self.manager, 'current', 'editar_dados')
        )

        # Itens Específicos
        if tipo == "Paciente":
            self.adicionar_item(
                menu_list, 
                "Meu Psicólogo", 
                "Ver profissional vinculado", 
                "doctor", 
                self.ver_meu_psicologo
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
        
        self.adicionar_item(
            menu_list,
            "Alterar Senha",
            "Definir nova senha de acesso",
            "lock-reset",
            self.mostrar_dialogo_senha # Chama a função abaixo
        )

        # Logout
        self.adicionar_item(
            menu_list, 
            "Sair do App", 
            "", 
            "logout", 
            self.fazer_logout,
            is_logout=True
        )

    def adicionar_item(self, container, titulo, subtitulo, icone, acao, is_logout=False):
        cor_icone = "#F44336" if is_logout else "#92C7A3"
        cor_texto = "Error" if is_logout else "Primary"
        
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
            md_bg_color=[1, 1, 1, 1], 
            radius=[16],
            pos_hint={"center_x": .5},
            on_release=acao
        )
        
        if subtitulo:
            item.add_widget(MDListItemSupportingText(text=subtitulo))
            
        container.add_widget(item)
    
    def ver_meu_psicologo(self, *args):
        """
        Busca e exibe os dados do profissional vinculado a este paciente.
        """
        try:
            db = self.get_db()
            paciente_id = self.get_user_id()
            
            # 1. Descobre o ID do psicólogo
            psicologo_id = db.get_psicologo_id_by_paciente(paciente_id)
            
            if not psicologo_id:
                self.show_popup("Meu Psicólogo", "Você ainda não está vinculado a nenhum profissional.")
                return

            # 2. Busca os dados pessoais desse ID (Nome, Email)
            # Reutilizamos a função que já existe para buscar dados de usuário
            dados_psi = db.get_user_details(psicologo_id)
            
            if dados_psi:
                nome = dados_psi.get("username", "Desconhecido")
                email = dados_psi.get("email", "Não informado")
                
                mensagem = f"Profissional: {nome}\nContato: {email}"
                self.show_popup("Seu Psicólogo", mensagem)
            else:
                self.show_popup("Erro", "Vínculo encontrado, mas não foi possível carregar os dados do médico.")

        except Exception as e:
            print(f"Erro ao buscar psicólogo: {e}")
            self.show_popup("Erro", "Falha de conexão ao buscar dados.")
    
    # Importe MDTextField no topo do arquivo se não tiver:
    # from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

    def mostrar_dialogo_senha(self, *args):
        # Campos de texto
        self.field_old_pass = MDTextField(
            MDTextFieldHintText(text="Senha Atual"),
            mode="outlined",
        )
        # No KivyMD 2.0 para senha oculta, usamos password=True (se suportado) ou input_type
        self.field_old_pass.password = True 

        self.field_new_pass = MDTextField(
            MDTextFieldHintText(text="Nova Senha"),
            mode="outlined",
        )
        self.field_new_pass.password = True

        # Container vertical para os campos
        content = MDBoxLayout(
            self.field_old_pass,
            self.field_new_pass,
            orientation="vertical",
            spacing="15dp",
            adaptive_height=True,
            size_hint_y=None,
            height="160dp" # Ajuste conforme necessário
        )

        self.dialog_senha = MDDialog(
            MDDialogHeadlineText(text="Trocar Senha"),
            MDDialogContentContainer(content),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancelar"), style="text", on_release=lambda x: self.dialog_senha.dismiss()),
                MDButton(MDButtonText(text="Confirmar"), style="text", on_release=self.confirmar_troca_senha),
                spacing="8dp"
            )
        )
        self.dialog_senha.open()

    def confirmar_troca_senha(self, *args):
        old = self.field_old_pass.text.strip()
        new = self.field_new_pass.text.strip()

        if not old or not new:
            # Você pode usar um toast ou print se não quiser fechar o dialog
            print("Preencha os campos") 
            return

        # Chama o banco
        db = self.get_db()
        user_id = self.get_user_id()
        
        success, msg = db.change_password(user_id, old, new)
        
        self.dialog_senha.dismiss()
        self.show_popup("Aviso", msg) # Usa seu show_popup existente para o resultado

    def fazer_logout(self, *args):
        app = self.get_app()
        app.logged_user_id = None
        app.logged_user_name = None
        app.logged_user_type = None
        app.root.current = "main"
    
    

class EditarDadosScreen(BaseScreen):
    dialog = None

    def on_enter(self, *args):
        self.carregar_dados_atuais()

    # --- FUNÇÃO REMOVIDA DAQUI (calcular_e_exibir_idade) ---

    def carregar_dados_atuais(self):
        try:
            user_id = self.manager.app.logged_user_id
            db = self.manager.app.db
            
            dados = db.get_user_details(user_id)
            
            if dados:
                self.ids.field_username.text = dados.get("username", "")
                self.ids.field_email.text = dados.get("email", "")
                
                # Apenas carrega o texto da data, sem calcular nada
                data_nasc = dados.get("data_nascimento", "")
                self.ids.field_nasc.text = str(data_nasc)
                
                # --- LINHA REMOVIDA: self.calcular_e_exibir_idade(data_nasc) ---
                
            else:
                self.show_popup("Erro", "Não foi possível carregar seus dados.")

        except Exception as e:
            print(f"Erro no carregamento: {e}")

    def salvar_dados(self):
        # ... (seu código de salvar continua igual) ...
        db = self.get_db()
        user_id = self.get_user_id()
        
        username = self.ids.field_username.text.strip()
        email = self.ids.field_email.text.strip()
        nascimento = self.ids.field_nasc.text.strip()
        
        if not (username and email and nascimento):
            self.show_popup("Erro", "Todos os campos são obrigatórios.")
            return
            
        success, message = db.update_user_details(user_id, username, email, nascimento)
        
        if success:
            app = self.get_app()
            app.logged_user_name = username
            self.show_popup("Sucesso!", message)
            # Ao voltar para 'conta', lá sim a idade será recalculada corretamente
            self.manager.current = "conta" 
        else:
            self.show_popup("Erro ao Salvar", message)