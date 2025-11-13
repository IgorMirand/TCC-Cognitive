# app/ui/telas/diario.py
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from datetime import datetime
from app.ui.telas.register_activity import EMOCOES_MAP
import pytz
from kivy.factory import Factory

class DiarioScreen(MDScreen):
    def on_enter(self, *args):
        self.load_notas()
    
    def get_db(self):
        return self.manager.app.db
    
    def get_user_id(self):
        return self.manager.app.logged_user_id

    def get_icon_for_sentiment(self, sentimento_txt):
        s = sentimento_txt.lower()
        if "feliz" in s or "bem" in s or "ótimo" in s:
            return "emoticon-happy-outline", "#4CAF50"
        elif "triste" in s or "mal" in s:
            return "emoticon-sad-outline", "#F44336"
        elif "ansioso" in s or "estresse" in s:
            return "emoticon-cry-outline", "#FF9800"
        elif "neutro" in s:
            return "emoticon-neutral-outline", "#9E9E9E"
        return "emoticon-outline", "#92C7A3"

    def load_notas(self):
        tabela_container = self.ids.tabela_container
        tabela_container.clear_widgets()
        
        user_id = self.get_user_id()
        
        if not user_id:
            self.show_message("Faça login para ver seu diário.")
            return
            
        db = self.get_db()
        success, lista_notas = db.get_entradas_historico(user_id)
        
        if not success:
            self.show_message("Erro ao conectar ao banco de dados.")
            return
            
        if not lista_notas:
            self.show_message("Seu histórico está vazio. \nRegistre como foi seu dia!")
            return
        
        for (reg_id, data_iso, sentimento_id, anotacao, atividades_txt) in lista_notas:
            sentimento_txt = EMOCOES_MAP.get(sentimento_id, "Desconhecido")
            
            try:
                dt = datetime.fromisoformat(data_iso)
                dt_local = dt.astimezone(pytz.timezone('America/Sao_Paulo'))
                data_formatada = dt_local.strftime("%d/%m • %H:%M")
            except Exception:
                data_formatada = data_iso 

            icon_name, icon_color = self.get_icon_for_sentiment(sentimento_txt)

            # Instancia o card definido no KV
            card = Factory.DiarioCard()
            
            card.ids.lbl_sentimento.text = sentimento_txt
            card.ids.lbl_data.text = data_formatada
            card.ids.lbl_atividades.text = atividades_txt if atividades_txt else "Sem atividades registradas"
            card.ids.lbl_anotacao.text = anotacao if anotacao else "Sem anotações"
            
            card.ids.icon_sentimento.icon = icon_name
            card.ids.icon_sentimento.text_color = icon_color

            tabela_container.add_widget(card)

    def show_message(self, text):
        container = self.ids.tabela_container
        box = MDBoxLayout(orientation="vertical", size_hint_y=None, height="200dp", padding="20dp")
        
        # --- CORREÇÃO AQUI (KivyMD 2.0.0) ---
        label = MDLabel(
            text=text, 
            halign="center", 
            theme_text_color="Hint",
            font_style="Title", # Substitui 'H6'
            role="medium"       # Define o tamanho
        )
        
        box.add_widget(label)
        container.add_widget(box)