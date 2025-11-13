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
from kivy.properties import  NumericProperty, ListProperty
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingCheckbox, MDListItemSupportingText, MDListItemTertiaryText
from kivy.clock import Clock 

EMOCOES_MAP = {
    1: "Feliz",
    2: "Triste",
    3: "Medo",
    4: "Surpreso",
    5: "Raiva",
    6: "Envergonhado",
    7: "Constrangido",
    8: "Receoso",
    9: "Apático",
    10: "Deprimido",
    11: "Irritado"
}
    
class StepManager(ScreenManager): 
    etapa_atual = NumericProperty(1)
    
    nomes_etapas = ListProperty(['sentimento', 'register_activity', 'anotacao_dia'])
    
    def ir_proxima_etapa(self):
            self.transition.direction = 'left'

    def ir_etapa_anterior(self):
            self.transition.direction = 'right'
    
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

    # Em RegisterActivityScreen
    def do_register_activities(self):
        """
        MODIFICADO: Apenas coleta os IDs e passa para a próxima tela.
        NÃO SALVA MAIS NO BANCO.
        """
        print("DEBUG (Atividades): 'do_register_activities' foi chamado.")
        
        ids_selecionados = []
        list_widget = self.ids.lista_selecao_atividades

        for item in list_widget.children:
            if hasattr(item, 'my_checkbox_ref'):
                if item.my_checkbox_ref.active:
                    ids_selecionados.append(item.my_checkbox_ref.atividade_id)
        
        # --- MUDANÇA PRINCIPAL ---
        # Nós aceitamos 0 atividades. NÃO mostre um popup de erro.
        
        # 1. Guarda os IDs (mesmo que seja uma lista vazia)
        self.manager.app.temp_entry_data['atividades_ids'] = ids_selecionados
        print(f"DEBUG (Atividades): IDs {ids_selecionados} salvos. Indo para anotação.")

        # 2. Limpa os checkboxes
        for item in list_widget.children:
            if hasattr(item, 'my_checkbox_ref'):
                item.my_checkbox_ref.active = False
        
        # 3. Vai para a próxima tela
        self.manager.current = 'anotacao_dia'

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

    def on_enter(self, *args):
        # Reseta os dados temporários e carrega os sentimentos
        self.manager.app.temp_entry_data = {}
        self.carregar_sentimentos()

    def carregar_sentimentos(self):
        """
        Cria a lista de sentimentos com checkboxes de seleção única.
        """
        list_widget = self.ids.lista_sentimentos
        list_widget.clear_widgets()

        # Usa o dicionário global EMOCOES_MAP
        for sentimento_id, sentimento_texto in EMOCOES_MAP.items():
            
            list_item = MDListItem()
            list_item.add_widget(MDListItemHeadlineText(text=sentimento_texto))
            
            checkbox = MDListItemTrailingCheckbox(
                # --- A CHAVE PARA SELEÇÃO ÚNICA ---
                group="sentimentos_group" 
            )
            # Salva o ID do sentimento (ex: 1) no checkbox
            checkbox.sentimento_id = sentimento_id 
            
            list_item.add_widget(checkbox)

            # Usa nossa referência manual (a prova de bugs)
            list_item.my_checkbox_ref = checkbox
            
            list_widget.add_widget(list_item)

    def ir_para_atividades(self):
        """
        Pega o sentimento selecionado e o salva temporariamente antes de ir
        para a próxima tela.
        """
        sentimento_selecionado_id = None
        list_widget = self.ids.lista_sentimentos

        # Loop para encontrar qual checkbox está ativo
        for item in list_widget.children:
            if hasattr(item, 'my_checkbox_ref'):
                checkbox_widget = item.my_checkbox_ref
                if checkbox_widget.active:
                    sentimento_selecionado_id = checkbox_widget.sentimento_id
                    break # Encontramos (só pode haver um)
        
        # Verifica se o usuário selecionou algo
        if sentimento_selecionado_id is None:
            # (Opcional: mostrar popup de erro)
            print("ERRO: Nenhum sentimento selecionado.")
            # (Você precisará de uma função show_popup nesta classe)
            # self.show_popup("Atenção", "Você precisa selecionar um sentimento.")
            return

        # Guarda o ID do sentimento (ex: 1) no dicionário temporário do App
        self.manager.app.temp_entry_data['sentimento_id'] = sentimento_selecionado_id
        print(f"DEBUG (Sentimento): ID {sentimento_selecionado_id} salvo. Indo para atividades.")
        
        # Vai para a próxima tela
        self.manager.current = 'register_activity'
class AnotacaoDiaScreen(Screen):
    
    def on_enter(self):
        # Reseta os campos quando entra na tela (opcional)
        pass

    def salvar_nova_anotacao(self):
        """Coleta todas as respostas, formata em um texto único e salva."""
        
        # 1. Coleta os textos dos Inputs
        p1 = self.ids.input_humor.text.strip() or "Não respondeu"
        p2 = self.ids.input_desconforto.text.strip() or "Não respondeu"
        p3 = int(self.ids.slider_bem_estar.value) # Valor de 0 a 10
        p4 = self.ids.input_desafio.text.strip() or "Não respondeu"
        p5 = self.ids.input_medo.text.strip() or "Não respondeu"
        p6 = self.ids.input_vitoria.text.strip() or "Não respondeu"

        # 2. Coleta Autocuidado (Checkboxes)
        cuidados = []
        if self.ids.check_sono.active: cuidados.append("Sono")
        if self.ids.check_alimentacao.active: cuidados.append("Alimentação")
        if self.ids.check_movimento.active: cuidados.append("Movimento")
        p_autocuidado = ", ".join(cuidados) if cuidados else "Nenhum específico"

        # 3. Formata o texto final para salvar no banco (campo 'anotacao')
        texto_consolidado = (
            f"1. Influência no humor: {p1}\n"
            f"2. Desconforto/Estresse: {p2}\n"
            f"3. Nota Bem-estar: {p3}/10\n"
            f"4. Maior desafio: {p4}\n"
            f"5. Evitou algo (medo): {p5}\n"
            f"6. Autocuidado: {p_autocuidado}\n"
            f"7. Vitória do dia: {p6}"
        )

        try:
            temp_data = self.manager.app.temp_entry_data
            user_id = self.get_user_id()
            db = self.get_db()
            
            # Verifica se tem dados anteriores
            sentimento_id = temp_data.get('sentimento_id', 1) # Default 1 se der erro
            atividades_ids = temp_data.get('atividades_ids', [])
            
            if not user_id:
                print("Usuário não logado.")
                return 
            
            data_hora_agora = datetime.now(pytz.utc).isoformat()
            
            # Salva no banco usando o texto consolidado
            success, msg = db.add_entrada_completa_diario(
                user_id, data_hora_agora, sentimento_id, texto_consolidado, atividades_ids
            )
            
            if success:
                print("Diário completo salvo!")
                self.limpar_campos()
                self.manager.app.temp_entry_data = {} 
                self.manager.current = 'home' 
            else:
                print(f"Erro ao salvar: {msg}")

        except Exception as e:
            print(f"Erro ao salvar: {e}")
    
    def limpar_campos(self):
        self.ids.input_humor.text = ""
        self.ids.input_desconforto.text = ""
        self.ids.input_desafio.text = ""
        self.ids.input_medo.text = ""
        self.ids.input_vitoria.text = ""
        self.ids.slider_bem_estar.value = 5
        self.ids.check_sono.active = False
        self.ids.check_alimentacao.active = False
        self.ids.check_movimento.active = False

    def get_db(self):
        return self.manager.app.db

    def get_user_id(self):
        return self.manager.app.logged_user_id