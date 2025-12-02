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
        
        # Ordena a lista pela data (Decrescente)
        lista_notas.sort(key=lambda x: x[1], reverse=True)
        
        for (reg_id, data_iso, sentimento_id, anotacao, atividades_txt) in lista_notas:
            sentimento_txt = EMOCOES_MAP.get(sentimento_id, "Desconhecido")
            
            # --- CORREÇÃO DA DATA AQUI ---
            try:
                dt = None
                # 1. Tenta o padrão ISO estrito (YYYY-MM-DDTHH:MM:SS)
                try:
                    dt = datetime.fromisoformat(data_iso)
                except ValueError:
                    # 2. Se falhar (ex: 2025-9-5...), tenta parse manual flexível
                    # O strptime aceita digitos unicos
                    dt = datetime.strptime(data_iso, "%Y-%m-%dT%H:%M:%S")

                # 3. Garante Fuso Horário
                if dt:
                    # Se a data não tiver info de fuso, assume UTC para converter corretamente
                    if dt.tzinfo is None:
                        dt = pytz.utc.localize(dt)
                    
                    dt_local = dt.astimezone(pytz.timezone('America/Sao_Paulo'))
                    data_formatada = dt_local.strftime("%d/%m • %H:%M")
                else:
                    data_formatada = data_iso # Fallback
                    
            except Exception as e:
                # Se tudo falhar, mostra a data crua
                print(f"Erro data: {e}") 
                data_formatada = data_iso 
            # -----------------------------

            icon_name, icon_color = self.get_icon_for_sentiment(sentimento_txt)

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
        
        label = MDLabel(
            text=text, 
            halign="center", 
            theme_text_color="Hint",
            font_style="Title",
            role="medium"
        )
        
        box.add_widget(label)
        container.add_widget(box)