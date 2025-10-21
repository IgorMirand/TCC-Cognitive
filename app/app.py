from kivy.core.window import Window
from kivy.app import App
from app.ui.manager import ScreenController

# Simula dimensão mobile durante dev no desktop (opcional)
Window.size = (440, 956)

class CognitiveApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # banco compartilhado
        #self.db = Database("users.db")

    def build(self):
        self.title = "Cognitive"
        controller = ScreenController(app=self)
        return controller
