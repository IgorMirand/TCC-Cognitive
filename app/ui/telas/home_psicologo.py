# app/ui/telas/home_psicologo.py

from kivymd.uix.screen import MDScreen


class PsychoHomeScreen(MDScreen):

    def on_enter(self, *args):
        """
        Chamado sempre que a tela é exibida.
        Usamos isto para carregar os dados do psicólogo.
        """
        self.load_user_data()

    def load_user_data(self):
        """
        Carrega os dados do utilizador logado.
        """
        try:
            # Pega o ID do utilizador que guardámos no login
            user_id = self.manager.app.logged_user_id

            # Atualiza o label
            # (Pode formatar o ID como quiser, ex: f"ID-P: {user_id:04d}")
            self.ids.id_label.text = f"ID : {user_id}"

        except AttributeError:
            # Lida com o caso de o 'logged_user_id' não estar definido
            self.ids.id_label.text = "ID : N/A"
        except Exception as e:
            print(f"Erro ao carregar dados do psicólogo: {e}")
            self.ids.id_label.text = "ID : Erro"

    def navigate_to(self, screen_name):
        """
        Função para navegar para outras telas (Pacientes, Estatisticas, etc.)
        """
        # Certifique-se de que estas telas existem no seu ScreenManager
        # self.manager.current = screen_name
        print(f"Navegando para: {screen_name}")