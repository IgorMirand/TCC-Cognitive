from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.lang import Builder
from pathlib import Path
#--- IMPORTA TODAS AS CLASSES QUE VAI GERIR ---
from app.ui.telas.home import HomeScreen
from app.ui.telas.home_psicologo import PsychoHomeScreen
from app.ui.telas.login import LoginScreen
from app.ui.telas.main import MainScreen
from app.ui.telas.register import RegisterScreen
from app.ui.telas.diario import DiarioScreen
from app.ui.telas.register_activity import RegisterActivityScreen, SentimentoScreen, AnotacaoDiaScreen
from app.ui.telas.register_activity import RegisterActivityScreen
from app.ui.telas.consulta_anotacao import ConsultaAnotacaoScreen, AdicionarAtividade


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
        self.add_widget(LoginScreen(name="login"))
        self.add_widget(RegisterScreen(name="register"))
        self.add_widget(DiarioScreen(name="diario"))
        self.add_widget(SentimentoScreen(name="sentimento"))
        self.add_widget(MainScreen(name="main"))
        self.add_widget(PsychoHomeScreen(name="home_psicologo"))
        self.add_widget(RegisterActivityScreen(name="register_activity"))
        self.add_widget(ConsultaAnotacaoScreen(name="consulta_anotacao"))
        self.add_widget(AdicionarAtividade(name="adicionar_atividade"))
        self.add_widget(AnotacaoDiaScreen(name="anotacao_dia"))

        # Mudei a tela inicial para "main", que parece ser sua tela
        # de boas-vindas. Se for "login", apenas mude aqui.
        self.current = "main"