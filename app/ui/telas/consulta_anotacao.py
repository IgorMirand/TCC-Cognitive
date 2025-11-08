from kivymd.uix.screen import Screen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon
from datetime import datetime
import pytz # (Lembre-se: pip install pytz)

# (Copie/Cole estas importações do seu login.py - são para o pop-up)
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText # <-- NOVO

class ConsultaAnotacaoScreen(Screen):
    dialog = None
    menu_pacientes = None
    pacientes_map = {} # Dicionário para guardar { "Nome do Paciente": id }
    paciente_selecionado_id = None

    def on_pre_enter(self, *args):
        """Chamado antes da tela ser exibida. Carrega os pacientes."""
        self.load_lista_pacientes()

    def get_db(self):
        return self.manager.app.db
    
    def get_user_id(self):
        # Neste ecrã, o utilizador logado é o Psicólogo
        return self.manager.app.logged_user_id

    def load_lista_pacientes(self):
        """Busca os pacientes no DB e cria o menu dropdown."""
        psicologo_id = self.get_user_id()
        if not psicologo_id:
            self.show_popup("Erro", "Não foi possível identificar o psicólogo.")
            return

        db = self.get_db()
        lista_pacientes_db = db.get_pacientes_do_psicologo(psicologo_id)
        
        self.pacientes_map = {} # Limpa o mapa
        menu_items = []
        
        for paciente_id, paciente_username in lista_pacientes_db:
            # Guarda o ID do paciente associado ao seu nome
            self.pacientes_map[paciente_username] = paciente_id
            
            # Cria o item para o menu
            menu_items.append(
                MDListItem(
                    MDListItemLeadingIcon(
                        icon="account-outline",
                    ),
                    text=paciente_username,
                    on_release=lambda x=paciente_username: self.on_paciente_select(x),
                )
            )
        
        # Cria o DropdownMenu
        self.menu_pacientes = MDDropdownMenu(
            caller=self.ids.paciente_selector_field, # "Chama" a partir do campo de texto
            items=menu_items,
            width_mult=4, # Largura do menu
        )

    def open_patient_menu(self):
        """Abre o menu dropdown de pacientes."""
        if self.menu_pacientes:
            self.menu_pacientes.open()

    def on_paciente_select(self, nome_paciente):
        """Chamado quando um paciente é selecionado no menu."""
        self.paciente_selecionado_id = self.pacientes_map.get(nome_paciente)
        self.ids.paciente_selector_field.text = nome_paciente # Atualiza o texto do campo
        self.menu_pacientes.dismiss() # Fecha o menu
        print(f"Paciente selecionado: {nome_paciente} (ID: {self.paciente_selecionado_id})")

    def salvar_anotacao(self):
        """Salva a anotação da consulta no banco de dados."""
        anotacao_texto = self.ids.anotacao_input.text.strip()
        
        # Validação
        if not self.paciente_selecionado_id:
            self.show_popup("Erro", "Por favor, selecione um paciente.")
            return
        if not anotacao_texto:
            self.show_popup("Erro", "A anotação não pode estar vazia.")
            return

        psicologo_id = self.get_user_id()
        db = self.get_db()
        data_hora_agora = datetime.now(pytz.utc).isoformat() # Data/Hora em UTC

        success, msg = db.add_anotacao_consulta(
            psicologo_id, 
            self.paciente_selecionado_id, 
            anotacao_texto, 
            data_hora_agora
        )

        if success:
            self.show_popup("Sucesso", msg)
            # Limpa os campos
            self.ids.anotacao_input.text = ""
            self.ids.paciente_selector_field.text = "Selecione o Paciente"
            self.paciente_selecionado_id = None
        else:
            self.show_popup("Erro ao Salvar", msg)

    # (Use a sua função show_popup corrigida para KivyMD 2.0.0)
    def show_popup(self, title, message):
        if self.dialog:
            self.dialog.dismiss()
        
        ok_button = MDButton(
            text="OK",
            style="text",
            on_release=self.close_dialog,
        )
        button_container = MDDialogButtonContainer(spacing="8dp")
        button_container.add_widget(ok_button)
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            [button_container],
            auto_dismiss=False,
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

class AdicionarAtividade(Screen):
    dialog = None
    add_dialog = None

    def save_new_activity_callback(self, *args):
        nova_atividade = self.ids.new_activity_input.text.strip()
        
        if not nova_atividade:
            self.show_popup("Atenção", "O nome da atividade não pode ser vazio.")
            return

        try:
            user_id = self.get_user_id()
            db = self.get_db()
            
            if not user_id:
                print("Usuário não logado.")
                return # (Mostrar pop-up "Faça login")
            
            success, msg = db.add_atividade_template(nova_atividade, user_id)
            
            if success:
                self.close_add_dialog()
                self.show_popup("Sucesso", f"Atividade '{nova_atividade}' adicionada!")
                self.ids.new_activity_input.text = ""
            else:
                self.show_popup("Erro", msg)

        except Exception as e:
            print("Erro", f"Falha ao salvar: {e}")
            self.show_popup("Erro", f"Falha ao salvar: {e}")

    def show_popup(self, title, message):
        self.close_message_dialog()

        close_button = MDButton(
            MDButtonText(text="OK"),
            style="text",
            on_release=self.close_message_dialog
        )
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            MDDialogButtonContainer(close_button, spacing="8dp")
        )
        self.dialog.open()

    def close_message_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    def close_add_dialog(self, *args):
        if self.add_dialog:
            self.add_dialog.dismiss()
            self.add_dialog = None

    def get_db(self):
        return self.manager.app.db
    
    def get_user_id(self):
        return self.manager.app.logged_user_id
