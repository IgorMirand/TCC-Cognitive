from kivy.uix.screenmanager import Screen
import sys
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from kivy.clock import Clock

# Dados de exemplo (Mock data)
MOCK_ROW_DATA = [
    ("25/06/2025 - 12:30:03", "Feliz", "Ouvi musicas"),
    ("25/06/2025 - 18:45:10", "Relaxado", "Caminhada no parque"),
    ("26/06/2025 - 09:00:00", "Produtivo", "Estudei KivyMD"),
    # Mais dados simulados para preencher a tabela
    *[(f"27/06/2025 - {i:02d}:00:00", "Neutro", "Trabalho") for i in range(1, 10)]
]

class DiarioScreen(Screen):
    def create_data_table(self, dt):
        """Cria e anexa o MDDataTable ao layout."""

        # Definição das colunas com seus nomes e larguras
        column_headers = [
            ("Data", dp(50)),
            ("Sentimento", dp(30)),
            ("Atividade", dp(50)),
        ]

        self.data_table = MDDataTable(
            # Ajustes de estilo para coincidir com a imagem
            background_color_header=[0.9, 0.9, 0.9, 1],
            background_color_cell=[0.95, 0.95, 0.95, 1],
            column_data=column_headers,
            row_data=MOCK_ROW_DATA,
            elevation=0,  # Remove sombra para um visual mais flat
            use_pagination=False,
            size_hint=(1, 1),  # Ocupa todo o espaço do container
        )

        # Adiciona a tabela ao BoxLayout definido no KV (id: table_container)
        if 'table_container' in self.ids:
            self.ids.table_container.add_widget(self.data_table)

    def on_nav_button_press(self, screen_name):
        """Manipulador genérico para os botões de navegação."""
        print(f"Navegação para: {screen_name} (Funcionalidade a ser implementada)")
        # Aqui, em um sistema real, você usaria um ScreenManager para trocar de tela
        # self.manager.current = screen_name