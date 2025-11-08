import pytz 
from datetime import datetime
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.dialog import (
    MDDialog, 
    MDDialogHeadlineText, 
    MDDialogSupportingText, 
    MDDialogButtonContainer
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.boxlayout import MDBoxLayout 
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingCheckbox, MDListItemSupportingText
from kivy.clock import Clock 

class StepManager(ScreenManager): 
    etapa_atual = NumericProperty(1)
    
    nomes_etapas = ListProperty(['sentimento', 'register_activity', 'anotacao_dia'])
    
    def ir_proxima_etapa(self):
            self.transition.direction = 'left'

    def ir_etapa_anterior(self):
            self.transition.direction = 'right'

class Barras(MDBoxLayout):
    manager = ObjectProperty(None) 
    
class RegisterActivityScreen(Screen):
    dialog = None
    add_dialog = None 
    chip_widgets = ListProperty([])

    def on_enter(self, *args):
        """
        Chamado sempre que a tela é exibida.
        Carrega os dados do banco de dados.
        """
        print("RegisterActivityScreen: on_enter")
        # Adia a busca para garantir que tudo esteja pronto
        Clock.schedule_once(self.carregar_dados_tela)

    def carregar_dados_tela(self, *args):
        """Chama as duas funções de carregamento."""
        self.carregar_chips_disponiveis()
        self.carregar_atividades_historico()

    def carregar_chips_disponiveis(self):
        """
        Carrega a lista de seleção de atividades (com checkboxes).
        (VERSÃO COM REFERÊNCIA DIRETA)
        """
        db = self.get_db()
        if not db: return

        list_widget = self.ids.lista_selecao_atividades
        list_widget.clear_widgets()

        success, atividades = db.get_atividades_template()

        if not success or not atividades:
            list_widget.add_widget(
                MDListItem(
                    MDListItemHeadlineText(text="Nenhuma atividade modelo encontrada.")
                )
            )
            return

        print(f"Encontrados {len(atividades)} modelos de atividade para seleção.")

        for atividade_id, atividade_texto in atividades:
            
            list_item = MDListItem()
            list_item.add_widget(MDListItemHeadlineText(text=atividade_texto))
            
            checkbox = MDListItemTrailingCheckbox()
            checkbox.atividade_id = atividade_id # Salva o ID no checkbox
            
            list_item.add_widget(checkbox)

            # --- A CORREÇÃO DEFINITIVA ---
            # Criamos nossa própria referência ao checkbox no item PAI
            list_item.my_checkbox_ref = checkbox
            # -------------------------------
            
            list_widget.add_widget(list_item)

    def do_register_activities(self):
        """
        Coleta os IDs dos checkboxes marcados e salva no banco de dados.
        (VERSÃO COM REFERÊNCIA DIRETA)
        """
        user_id = self.get_user_id()
        db = self.get_db()

        if not user_id or not db:
            self.show_popup("Erro", "Não foi possível conectar ao banco. Faça login novamente.")
            return

        ids_selecionados = []
        list_widget = self.ids.lista_selecao_atividades

        # Itera sobre os MDListItems na lista
        for item in list_widget.children:
            
            # --- CORREÇÃO PRINCIPAL ---
            # Verifica se o item tem nossa referência customizada
            if hasattr(item, 'my_checkbox_ref'):
                
                checkbox_widget = item.my_checkbox_ref
                
                # Agora sim, podemos checar com segurança
                if checkbox_widget.active:
                    try:
                        ids_selecionados.append(checkbox_widget.atividade_id)
                    except AttributeError:
                        print(f"ERRO: Checkbox {checkbox_widget} não tem 'atividade_id'!")
            # --- FIM DA CORREÇÃO ---
        
        if not ids_selecionados:
            self.show_popup("Atenção", "Você não selecionou nenhuma atividade.")
            return
        
        try:
            # Pega o timestamp
            data_hora_agora = datetime.now(pytz.utc).isoformat()
            
            success, msg = db.registrar_atividades_paciente(user_id, ids_selecionados, data_hora_agora)
            
            if success:
                # Desativa os checkboxes (usando a mesma referência)
                for item in list_widget.children:
                    if hasattr(item, 'my_checkbox_ref'):
                        item.my_checkbox_ref.active = False
                            
                self.show_popup("Sucesso", "Suas atividades foram registradas!")
                self.carregar_atividades_historico() # Atualiza o histórico
                self.manager.current = 'anotacao_dia'
            else:
                self.show_popup("Erro", msg)

        except Exception as e:
            print(f"Erro ao tentar registrar atividades: {e}")
            self.show_popup("Erro", "Não foi possível salvar. Verifique se está logado.")

    # 3. Para o PACIENTE salvar as atividades que ele selecionou
    def registrar_atividades_paciente(self, paciente_id, lista_de_ids_atividades, data_hora_iso):
        """
        Registra as atividades que o paciente selecionou.
        Recebe o ID do paciente, uma LISTA de IDs de atividades e o timestamp ISO.
        """
        try:
            with self.connect() as conn:
                with conn.cursor() as cursor:
                    
                    # Prepara os dados como uma lista de tuplas
                    # ex: [(15, 1, 'timestamp...'), (15, 3, 'timestamp...')]
                    dados_para_inserir = [
                        (paciente_id, atividade_id, data_hora_iso) 
                        for atividade_id in lista_de_ids_atividades
                    ]

                    # Esta é uma forma otimizada de inserir múltiplos registros
                    from psycopg2.extras import execute_values
                    query = """
                        INSERT INTO registros_atividades_paciente 
                            (paciente_id, atividade_template_id, data_hora_iso) 
                        VALUES %s
                    """
                    
                    execute_values(cursor, query, dados_para_inserir)
                    
                    conn.commit()
                    return True, "Atividades registradas com sucesso."
        except Exception as e:
            if conn: conn.rollback()
            print(f"[ERRO] registrar_atividades_paciente: {e}")
            return False, "Erro ao registrar atividades."


    def carregar_atividades_historico(self):
        """
        Carrega o HISTÓRICO do paciente (atividades já registradas).
        Usa a lista 'lista_atividades'.
        """
        user_id = self.get_user_id()
        db = self.get_db()

        if not user_id or not db:
            print("Usuário ou DB não encontrado, não posso carregar histórico.")
            return

        list_widget = self.ids.lista_atividades
        list_widget.clear_widgets()

        # 2. Busca o histórico de registros do paciente
        success, registros = db.get_registros_do_paciente(user_id)

        if not success:
            list_widget.add_widget(
                MDListItem(MDListItemHeadlineText(text="Erro ao carregar histórico."))
            )
            return
        

        # O retorno é [('Texto Ativ 1', data1), ('Texto Ativ 2', data2)]
        print(f"Encontrados {len(registros)} registros de histórico.")
        for atividade_texto, data_registro in registros:
            item = MDListItem(
                MDListItemHeadlineText(text=atividade_texto),
                MDListItemSupportingText(text=str(data_registro)) # Mostra a data
            )
            list_widget.add_widget(item)

    

    # --- Funções de Popup e Getters (Sem Mudanças) ---

    def show_popup(self, title, message):
        self.close_dialog() # Chama a função unificada

        close_button = MDButton(
            MDButtonText(text="OK"),
            style="text",
            on_release=self.close_dialog
        )
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            MDDialogButtonContainer(
                close_button,
                spacing="8dp"
            )
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
        # Fecha também o dialog de adicionar (se existir)
        if self.add_dialog:
            self.add_dialog.dismiss()
            self.add_dialog = None

    def get_db(self):
        # Proteção para garantir que app e db existam
        if hasattr(self.manager, 'app') and hasattr(self.manager.app, 'db'):
            return self.manager.app.db
        return None

    def get_user_id(self):
        # Proteção para garantir que app e user_id existam
        if hasattr(self.manager, 'app') and hasattr(self.manager.app, 'logged_user_id'):
            return self.manager.app.logged_user_id
        return None
    
class SentimentoScreen(Screen):
    pass

class AnotacaoDiaScreen(Screen):
    def salvar_nova_anotacao(self):
        """Salva a nova anotação do MDTextField no banco de dados."""
        texto = self.ids.nova_anotacao_input.text.strip()
        if not texto:
            print("Anotação vazia.")
            return # (Opcional: mostrar pop-up de erro)
            
        try:
            user_id = self.get_user_id()
            db = self.get_db()
            
            if not user_id:
                print("Usuário não logado.")
                return # (Mostrar pop-up "Faça login")
            
            # Pega a data/hora ATUAL em formato ISO 8601 (UTC é o padrão)
            data_hora_agora = datetime.now(pytz.utc).isoformat()
            
            success, msg = db.add_anotacao_diario(user_id, texto, data_hora_agora)
            
            if success:
                print("Anotação salva!")
                self.ids.nova_anotacao_input.text = "" # Limpa o campo
            else:
                print(f"Erro ao salvar: {msg}") # (Mostrar pop-up de erro)

        except Exception as e:
            print(f"Erro ao salvar: {e}")
    
    def get_db(self):
        return self.manager.app.db

    def get_user_id(self):
        return self.manager.app.logged_user_id