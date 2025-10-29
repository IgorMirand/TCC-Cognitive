from kivy.uix.screenmanager import ScreenManager, SlideTransition, WipeTransition
from app.ui.telas.home import HomeScreen
from app.ui.telas.home_psicologo import PsychoHomeScreen
from app.ui.telas.login import LoginScreen
from app.ui.telas.main import MainScreen
from app.ui.telas.notifications import Notification
from app.ui.telas.register import RegisterScreen,RegisterScreen1
from app.ui.telas.diario import DiarioScreen
from app.ui.telas.register_activity import RegisterActivityScreen, SentimentoScreen
from kivy.lang import Builder
from pathlib import Path

# Carrega styles.kv automaticamente
kv_path = Path(__file__).parent / "styles.kv"
if kv_path.exists():
    Builder.load_file(str(kv_path))


class ScreenController(ScreenManager):
    def __init__(self, app, **kwargs):
        super().__init__(transition=SlideTransition(), **kwargs)
        self.app = app

        # adiciona telas (Toda a lógica está centralizada aqui)
        self.add_widget(HomeScreen(name="home"))
        self.add_widget(Notification(name="notifications"))
        self.add_widget(LoginScreen(name="login"))
        self.add_widget(RegisterScreen(name="register"))
        self.add_widget(RegisterScreen1(name="register1"))
        self.add_widget(DiarioScreen(name="diario"))
        self.add_widget(SentimentoScreen(name="sentimento"))
        self.add_widget(MainScreen(name="main"))
        self.add_widget(PsychoHomeScreen(name="home_psicologo"))
        self.add_widget(RegisterActivityScreen(name="register_activity"))

        # Mudei a tela inicial para "main", que parece ser sua tela
        # de boas-vindas. Se for "login", apenas mude aqui.
        self.current = "diario"