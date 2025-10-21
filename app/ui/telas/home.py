from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.utils import get_color_from_hex

class HomeScreen(Screen):
    def build(self):
        layout = MDBoxLayout(orientation='vertical')
        # Set background color using a hex value
        layout.md_bg_color = get_color_from_hex("#FF5733")  # Example hex color (orange-red)
        return layout

class NotificationScreen(Screen):
    pass
