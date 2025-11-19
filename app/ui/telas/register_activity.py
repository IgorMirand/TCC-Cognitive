import pytz 
from datetime import datetime
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock 
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingCheckbox
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import NumericProperty

# Mapa simples sem emojis
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
class StepIndicator(MDBoxLayout):
    current_step = NumericProperty(1)
    
class StepManager(ScreenManager): 
    etapa_atual = NumericProperty(1)
    nomes_etapas = ListProperty(['sentimento', 'register_activity', 'anotacao_dia'])

# --- TELA 1: SENTIMENTOS ---
class SentimentoScreen(Screen):
    def on_enter(self, *args):
        self.manager.app.temp_entry_data = {}
        self.carregar_sentimentos()

    def carregar_sentimentos(self):
        """Carrega lista com Checkbox de seleção única."""
        list_widget = self.ids.lista_sentimentos
        list_widget.clear_widgets()

        for s_id, texto in EMOCOES_MAP.items():
            item = MDListItem()
            item.add_widget(MDListItemHeadlineText(text=texto))
            
            # Checkbox com 'group' garante que só um seja selecionado
            checkbox = MDListItemTrailingCheckbox(group="sentimentos")
            checkbox.sentimento_id = s_id
            
            item.add_widget(checkbox)
            item.my_checkbox = checkbox # Referência fácil
            
            list_widget.add_widget(item)

    def ir_para_atividades(self):
        selecionado = None
        for item in self.ids.lista_sentimentos.children:
            if hasattr(item, 'my_checkbox') and item.my_checkbox.active:
                selecionado = item.my_checkbox.sentimento_id
                break
        
        if not selecionado:
            print("Selecione um sentimento!")
            return

        self.manager.app.temp_entry_data['sentimento_id'] = selecionado
        self.manager.current = 'register_activity'

# --- TELA 2: ATIVIDADES ---
class RegisterActivityScreen(Screen):
    def on_enter(self, *args):
        Clock.schedule_once(self.carregar_chips_disponiveis)

    def carregar_chips_disponiveis(self, *args):
        db = self.get_db()
        if not db: return

        list_widget = self.ids.lista_selecao_atividades
        list_widget.clear_widgets()

        success, atividades = db.get_atividades_template()
        
        if not success or not atividades:
            list_widget.add_widget(MDListItem(MDListItemHeadlineText(text="Nenhuma atividade encontrada.")))
            return

        for atv_id, texto in atividades:
            item = MDListItem()
            item.add_widget(MDListItemHeadlineText(text=texto))
            
            # Checkbox sem grupo (múltipla escolha)
            checkbox = MDListItemTrailingCheckbox()
            checkbox.atividade_id = atv_id
            
            item.add_widget(checkbox)
            item.my_checkbox = checkbox
            
            list_widget.add_widget(item)

    def do_register_activities(self):
        ids_selecionados = []
        for item in self.ids.lista_selecao_atividades.children:
            if hasattr(item, 'my_checkbox') and item.my_checkbox.active:
                ids_selecionados.append(item.my_checkbox.atividade_id)
        
        self.manager.app.temp_entry_data['atividades_ids'] = ids_selecionados
        self.manager.current = 'anotacao_dia'

    def get_db(self):
        if hasattr(self.manager, 'app') and hasattr(self.manager.app, 'db'):
            return self.manager.app.db
        return None

# --- TELA 3: REFLEXÃO ---
class AnotacaoDiaScreen(Screen):
    
    def salvar_nova_anotacao(self):
        # Coleta dados
        p1 = self.ids.input_humor.text
        p2 = self.ids.input_desconforto.text
        p3 = int(self.ids.slider_bem_estar.value)
        p4 = self.ids.input_desafio.text
        p5 = self.ids.input_medo.text
        p6 = self.ids.input_vitoria.text

        cuidados = []
        if self.ids.check_sono.active: cuidados.append("Sono")
        if self.ids.check_alimentacao.active: cuidados.append("Alimentação")
        if self.ids.check_movimento.active: cuidados.append("Movimento")
        p_autocuidado = ", ".join(cuidados) if cuidados else "Nenhum"

        texto_final = (
            f"1. Humor: {p1}\n2. Desconforto: {p2}\n3. Bem-estar: {p3}/10\n"
            f"4. Desafio: {p4}\n5. Medo: {p5}\n6. Autocuidado: {p_autocuidado}\n7. Vitória: {p6}"
        )

        try:
            user_id = self.manager.app.logged_user_id
            db = self.manager.app.db
            temp = self.manager.app.temp_entry_data
            
            success, msg = db.add_entrada_completa_diario(
                user_id, 
                datetime.now(pytz.utc).isoformat(),
                temp.get('sentimento_id', 1),
                texto_final,
                temp.get('atividades_ids', [])
            )
            
            if success:
                self.limpar_campos()
                self.manager.current = 'home'
            else:
                print(f"Erro ao salvar: {msg}")

        except Exception as e:
            print(f"Erro: {e}")

    def limpar_campos(self):
        self.ids.input_humor.text = ""
        self.ids.input_desconforto.text = ""
        self.ids.slider_bem_estar.value = 5
        self.ids.input_desafio.text = ""
        self.ids.input_medo.text = ""
        self.ids.input_vitoria.text = ""
        self.ids.check_sono.active = False
        self.ids.check_alimentacao.active = False
        self.ids.check_movimento.active = False