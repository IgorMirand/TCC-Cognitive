# app/ui/telas/diario.py
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from datetime import datetime
import pytz # Para datas (pip install pytz)

class DiarioScreen(MDScreen):

    def on_enter(self, *args):
        """Chamado sempre que a tela é exibida. Carrega as notas."""
        self.load_notas()
    
    def get_db(self):
        """Helper para pegar a instância do DB."""
        return self.manager.app.db
    
    def get_user_id(self):
        """Helper para pegar o ID do usuário logado."""
        return self.manager.app.logged_user_id

    def load_notas(self):
        """Busca as notas no DB e preenche a tabela (MDGridLayout)."""
        try:
            tabela_grid = self.ids.tabela_container
            tabela_grid.clear_widgets() # Limpa os dados antigos
            
            user_id = self.get_user_id()
            if not user_id:
                tabela_grid.add_widget(MDLabel(text="Faça login para ver seu diário.", halign="center", size_hint_x=2))
                return
                
            db = self.get_db()
            lista_notas = db.get_anotacoes_diario(user_id)
            
            if not lista_notas:
                # Adiciona um label que ocupa as 2 colunas
                tabela_grid.add_widget(MDLabel(text="Nenhuma anotação encontrada.", halign="center", size_hint_x=2))
                return

            # Para cada linha (tuplo) vinda do banco...
            for nota in lista_notas:
                data_iso, texto_anotacao = nota
                
                # Formata a data (de ISO para legível)
                try:
                    dt = datetime.fromisoformat(data_iso)
                    # Converte para o fuso horário local (opcional, mas recomendado)
                    dt_local = dt.astimezone(pytz.timezone('America/Sao_Paulo')) # Altere para o seu fuso
                    data_formatada = dt_local.strftime("%d/%m/%Y\n%H:%M:%S")
                except Exception as e:
                    print(f"Erro ao formatar data: {e}")
                    data_formatada = data_iso 

                # Adiciona o Label da Data (Coluna 1)
                tabela_grid.add_widget(MDLabel(
                    text=data_formatada,
                    halign="center",
                    theme_text_color="Primary",
                    adaptive_height=True,
                ))
                
                # Adiciona o Label da Anotação (Coluna 2)
                tabela_grid.add_widget(MDLabel(
                    text=texto_anotacao,
                    halign="left",
                    theme_text_color="Secondary",
                    adaptive_height=True,
                ))

        except Exception as e:
            print(f"Erro ao carregar notas: {e}")
            tabela_grid.clear_widgets()
            tabela_grid.add_widget(MDLabel(text="Erro ao carregar dados.", halign="center", size_hint_x=2))

    def salvar_nova_anotacao(self):
        """Salva a nova anotação do MDTextField no banco de dados."""
        texto = self.ids.nova_anotacao_input.text.strip()
        if not texto:
            print("Anotação vazia.")
            return # (Opcional: mostrar pop-up de erro)
            
        try:
            user_id = self.get_user_id()
            db = self.get_db()
            
            if not user_id:
                print("Usuário não logado.")
                return # (Mostrar pop-up "Faça login")
            
            # Pega a data/hora ATUAL em formato ISO 8601 (UTC é o padrão)
            data_hora_agora = datetime.now(pytz.utc).isoformat()
            
            success, msg = db.add_anotacao_diario(user_id, texto, data_hora_agora)
            
            if success:
                print("Anotação salva!")
                self.ids.nova_anotacao_input.text = "" # Limpa o campo
                self.load_notas() # Recarrega a lista
            else:
                print(f"Erro ao salvar: {msg}") # (Mostrar pop-up de erro)

        except Exception as e:
            print(f"Erro ao salvar: {e}")