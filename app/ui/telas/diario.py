from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen

class DiarioScreen(Screen):
    def on_nav_item_press(self, name):
        print(f"Selecionado: {name}")
