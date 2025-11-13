import os
from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from app.core.neon import Database
from app.ui.manager import ScreenController
from dotenv import load_dotenv

load_dotenv()
# Defina o tamanho da janela
Window.size = (440, 956)

# 2. Carregue TODOS os arquivos KV ANTES de tudo
Builder.load_file("app/ui/telas/login.kv")
Builder.load_file("app/ui/telas/register.kv")
Builder.load_file("app/ui/telas/home.kv")
Builder.load_file("app/ui/telas/conta.kv")
Builder.load_file("app/ui/telas/diario.kv")
Builder.load_file("app/ui/telas/main.kv")
Builder.load_file("app/ui/telas/home_psicologo.kv")
Builder.load_file("app/ui/telas/register_activity.kv")
Builder.load_file("app/ui/telas/consulta_anotacao.kv")


class CognitiveApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"

        # Tenta conectar à DB (com segurança)
        try:
            self.db = Database()
        except ValueError as e:
            print(f"--- ERRO CRÍTICO ---")
            print(f"Erro: {e}")
            print("Certifique-se que o ficheiro .env existe e NEON_DB_URL está definida.")
            print("----------------------")
            return None # Falha o arran

        # --- 5. VARIÁVEIS DE SESSÃO CORRIGIDAS ---
        self.logged_user_id = None
        self.logged_user_type = None

        # 3. Crie a instância do ScreenController
        sm = ScreenController(app=self)
        return sm

if __name__ == "__main__":
    CognitiveApp().run()