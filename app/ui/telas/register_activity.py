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
        """
        Coleta respostas, valida campos vazios colocando valores padrão
        e salva no banco de dados.
        """
        # 1. Coleta e Limpa (strip() remove espaços antes/depois)
        # Se o usuário digitar só espaços, vira string vazia ""
        raw_humor = self.ids.input_humor.text.strip()
        raw_desconforto = self.ids.input_desconforto.text.strip()
        raw_desafio = self.ids.input_desafio.text.strip()
        raw_medo = self.ids.input_medo.text.strip()
        raw_vitoria = self.ids.input_vitoria.text.strip()

        # 2. (Opcional) Bloqueio se tudo estiver vazio
        # Se quiser obrigar a escrever pelo menos o humor, descomente abaixo:
        if not raw_humor or not raw_desconforto or not raw_desafio or not raw_medo or not raw_vitoria:
            self.show_alert_dialog("Campo Obrigatório", "Por favor, conte-nos o que influenciou seu humor hoje.")
            return

        # 3. Define valores padrão (Fallback) para não salvar vazio no banco
        # A lógica é: valor = texto_digitado OU "Texto Padrão"
        p1 = raw_humor or "Não respondeu"
        p2 = raw_desconforto or "Nenhum desconforto citado"
        p3 = int(self.ids.slider_bem_estar.value)
        p4 = raw_desafio or "Nenhum desafio citado"
        p5 = raw_medo or "Não citou medos"
        p6 = raw_vitoria or "Nenhuma vitória citada"

        # 4. Coleta Autocuidado
        cuidados = []
        if self.ids.check_sono.active: cuidados.append("Sono")
        if self.ids.check_alimentacao.active: cuidados.append("Alimentação")
        if self.ids.check_movimento.active: cuidados.append("Movimento")
        p_autocuidado = ", ".join(cuidados) if cuidados else "Nenhum cuidado específico"

        # 5. Formata o texto final
        texto_final = (
            f"1. Humor: {p1}\n"
            f"2. Desconforto: {p2}\n"
            f"3. Bem-estar: {p3}/10\n"
            f"4. Desafio: {p4}\n"
            f"5. Medo: {p5}\n"
            f"6. Autocuidado: {p_autocuidado}\n"
            f"7. Vitória: {p6}"
        )

        # 6. Tenta Salvar
        try:
            app = self.manager.app
            user_id = app.logged_user_id
            db = app.db
            temp = app.temp_entry_data
            
            # Verifica se temos os dados anteriores (Sentimento e Atividades)
            sentimento_id = temp.get('sentimento_id', 1) # Default 1 (Feliz) se der erro
            atividades_ids = temp.get('atividades_ids', [])

            success, msg = db.add_entrada_completa_diario(
                user_id, 
                datetime.now(pytz.utc).isoformat(),
                sentimento_id,
                texto_final,
                atividades_ids
            )
            
            if success:
                print("Sucesso: Diário salvo.")
                self.limpar_campos()
                self.manager.current = 'home'
            else:
                self.show_alert_dialog("Erro ao Salvar", msg)

        except Exception as e:
            print(f"Erro crítico ao salvar: {e}")
            self.show_alert_dialog("Erro", "Ocorreu um erro interno ao processar seus dados.")

    def show_alert_dialog(self, title, text):
        """Helper para mostrar erros na tela (KivyMD 2.0)"""
        # Fecha diálogo anterior se existir
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()
            
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                spacing="8dp",
            ),
        )
        self.dialog.open()

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