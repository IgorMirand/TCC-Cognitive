from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from app.core.neon import Database
from app.ui.manager import ScreenController

# Defina o tamanho da janela
Window.size = (440, 956)

# 2. Carregue TODOS os arquivos KV ANTES de tudo
Builder.load_file("app/ui/telas/login.kv")
Builder.load_file("app/ui/telas/register.kv")
Builder.load_file("app/ui/telas/home.kv")
Builder.load_file("app/ui/telas/diario.kv")
Builder.load_file("app/ui/telas/sentimento.kv")
Builder.load_file("app/ui/telas/main.kv")
Builder.load_file("app/ui/telas/notifications.kv")
Builder.load_file("app/ui/telas/home_psicologo.kv")
Builder.load_file("app/ui/telas/register_activity.kv")


class CognitiveApp(MDApp):
    def build(self):
        self.db = Database()
        self.logged_user = None

        # 3. Crie a instância do ScreenController
        #    Ele agora é o seu widget 'root'
        #    Passamos 'self' (a instância do app) para ele
        sm = ScreenController(app=self)
        return sm

if __name__ == "__main__":
    CognitiveApp().run()