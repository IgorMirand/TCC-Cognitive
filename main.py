import os
import sys  # <-- 1. Importe o 'sys'
from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from app.core.neon import Database
from app.ui.manager import ScreenController
from dotenv import load_dotenv
from kivy.resources import resource_add_path 


load_dotenv()
Window.size = (440, 956)

# --- 2. ADICIONE A FUNÇÃO 'resource_path' ---
def resource_path(relative_path):
    """ 
    Obtém o caminho absoluto para recursos.
    Funciona para modo 'dev' e para o executável do PyInstaller.
    """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver rodando como .exe, use o caminho normal
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if hasattr(sys, '_MEIPASS'):
    resource_add_path(os.path.join(sys._MEIPASS))

# --- 3. USE A FUNÇÃO 'resource_path' em TODOS os 'Builder.load_file' ---
Builder.load_file(resource_path("app/ui/telas/login.kv"))
Builder.load_file(resource_path("app/ui/telas/register.kv"))
Builder.load_file(resource_path("app/ui/telas/home.kv"))
Builder.load_file(resource_path("app/ui/telas/conta.kv"))
Builder.load_file(resource_path("app/ui/telas/diario.kv"))
Builder.load_file(resource_path("app/ui/telas/main.kv"))
Builder.load_file(resource_path("app/ui/telas/home_psicologo.kv"))
Builder.load_file(resource_path("app/ui/telas/register_activity.kv"))
Builder.load_file(resource_path("app/ui/telas/consulta_anotacao.kv"))


class CognitiveApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Green"

        try:
            self.db = Database()
        except ValueError as e:
            print(f"--- ERRO CRÍTICO ---")
            print(f"Erro: {e}")
            print("Certifique-se que o ficheiro .env existe e NEON_DB_URL está definida.")
            print("----------------------")
            return None 

        self.logged_user_id = None
        self.logged_user_type = None

        sm = ScreenController(app=self)
        return sm

if __name__ == "__main__":
    CognitiveApp().run()