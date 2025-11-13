from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from datetime import datetime
import pytz

class ConsultaAnotacaoScreen(MDScreen):
    dialog = None
    menu = None
    paciente_selecionado_id = None

    def on_enter(self, *args):
        """Chamado ao entrar na tela. Prepara o menu."""
        # --- MUDANÇA AQUI: Acessa o ID do texto, não do botão ---
        self.ids.lbl_btn_paciente.text = "Selecione o Paciente..."
        
        self.paciente_selecionado_id = None
        self.ids.anotacao_input.text = ""
        self.ids.lista_historico.clear_widgets()
        
        self.load_pacientes_menu()

    def get_db(self):
        return self.manager.app.db
    
    def get_user_id(self):
        return self.manager.app.logged_user_id

    def load_pacientes_menu(self):
        psicologo_id = self.get_user_id()
        db = self.get_db()
        
        # Busca lista [(id, "Nome"), ...]
        pacientes = db.get_pacientes_do_psicologo_com_nomes(psicologo_id)
        
        if not pacientes:
            self.ids.lbl_btn_paciente.text = "Nenhum paciente vinculado"
            self.ids.btn_selecionar_paciente.disabled = True
            return

        # --- CORREÇÃO KIVYMD 2.0: Lista de Dicionários ---
        menu_items = [
            {
                "text": nome_paciente,
                "on_release": lambda x=pid, y=nome_paciente: self.selecionar_paciente(x, y),
            } for pid, nome_paciente in pacientes
        ]
        
        self.menu = MDDropdownMenu(
            caller=self.ids.btn_selecionar_paciente,
            items=menu_items,
            position="bottom",
            width_mult=4,
            max_height="240dp",
        )
        self.ids.btn_selecionar_paciente.disabled = False

    def selecionar_paciente(self, paciente_id, nome_paciente):
        """
        Atualiza o ID interno E O TEXTO DO BOTÃO.
        """
        self.paciente_selecionado_id = paciente_id
        
        # --- MUDANÇA AQUI: Acessa o ID do texto, não do botão ---
        self.ids.lbl_btn_paciente.text = nome_paciente 
        
        self.menu.dismiss()
        self.load_historico(paciente_id)

    def load_historico(self, paciente_id):
        """Mostra o histórico assim que seleciona o paciente."""
        lista = self.ids.lista_historico
        lista.clear_widgets()
        
        db = self.get_db()
        psicologo_id = self.get_user_id()
        anotacoes = db.get_anotacoes_paciente(psicologo_id, paciente_id)
        
        if not anotacoes:
            lista.add_widget(MDLabel(text="Nenhuma anotação anterior.", halign="center", theme_text_color="Secondary"))
            return

        for an_id, data_iso, conteudo in anotacoes:
            try:
                data_fmt = data_iso.strftime("%d/%m/%Y às %H:%M")
            except:
                data_fmt = str(data_iso)

            card = MDCard(
                style="elevated",
                orientation="vertical",
                size_hint_y=None,
                height="100dp",
                padding="12dp",
                spacing="8dp",
                radius=[12],
                md_bg_color=[1,1,1,1]
            )
            card.add_widget(MDLabel(text=data_fmt, font_style="Label", role="large", bold=True, theme_text_color="Primary"))
            card.add_widget(MDLabel(text=conteudo, font_style="Body", role="medium", theme_text_color="Secondary", max_lines=3))
            lista.add_widget(card)

    def salvar_anotacao(self):
        texto = self.ids.anotacao_input.text.strip()
        
        if not self.paciente_selecionado_id:
            self.show_popup("Atenção", "Selecione um paciente primeiro.")
            return
        if not texto:
            self.show_popup("Atenção", "Escreva algo na anotação.")
            return

        db = self.get_db()
        psicologo_id = self.get_user_id()
        
        data_hora_agora = datetime.now(pytz.utc).isoformat()

        success, msg = db.salvar_anotacao_psicologo(psicologo_id, self.paciente_selecionado_id, texto, data_hora_agora)
        
        if success:
            self.show_popup("Sucesso", "Anotação salva!")
            self.ids.anotacao_input.text = ""
            self.load_historico(self.paciente_selecionado_id) # Atualiza a lista na hora
        else:
            self.show_popup("Erro", msg)

    def show_popup(self, title, text):
        if self.dialog: self.dialog.dismiss()
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=text),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="OK"), on_release=lambda x: self.dialog.dismiss())
            )
        )
        self.dialog.open()