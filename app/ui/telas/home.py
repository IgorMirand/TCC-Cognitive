from kivymd.uix.screen import Screen
from kivymd.uix.dialog import (
    MDDialog, 
    MDDialogHeadlineText, 
    MDDialogSupportingText,  
    MDDialogButtonContainer
)
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemLeadingIcon
from kivymd.uix.button import MDButton,MDButtonText, MDIconButton
from kivymd.uix.label import MDLabel,MDIcon
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from datetime import datetime
from kivy.core.clipboard import Clipboard
from kivymd.app import MDApp
import re


class HomeScreen(Screen):

    dialog = None

    def on_enter(self, *args):
        """Chamado sempre que a tela é exibida."""
        self.load_user_data()


    def load_user_data(self):
        """
        Carrega o NOME do paciente e verifica se ele JÁ TEM VÍNCULO
        para esconder o card de vincular.
        """
        try:
            # --- 1. Carregar nome de usuário ---
            if hasattr(self.manager.app, 'logged_user_name'):
                username = self.manager.app.logged_user_name
                # Use "Olá," para pacientes, "Dr(a)." é para psicólogos
                self.ids.id_label.text = f"Olá, {username}" 
            else:
                self.ids.id_label.text = "Bem-vindo(a), Paciente"

            # --- 2. Verificar Vínculo Existente ---
            db = self.manager.app.db
            paciente_id = self.manager.app.logged_user_id
            card = self.ids.vincula_card

            if not paciente_id:
                # Se não houver ID (erro de login?), não podemos checar.
                # Apenas mostramos o card como padrão.
                card.height = card.minimum_height
                card.opacity = 1
                card.disabled = False
                return

            # Busca o ID do psicólogo vinculado
            psicologo_id = db.get_psicologo_id_by_paciente(paciente_id)

            if psicologo_id:
                # PACIENTE JÁ VINCULADO: Esconder o card
                card.height = "0dp"
                card.opacity = 0
                card.disabled = True
            else:
                # PACIENTE SEM VÍNCULO: Mostrar o card
                # (Garante que ele apareça caso o estado mude)
                card.height = card.minimum_height # Força o 'adaptive_height'
                card.opacity = 1
                card.disabled = False
            
        except Exception as e:
            print(f"Erro ao carregar dados do Paciente: {e}")
            self.ids.id_label.text = "Bem-vindo"

            
    def vincula(self):
        """
        Chamado pelo botão "Vincular" no .kv.
        Tenta vincular este paciente (logado) usando o código do text field.
        """
        # Pega o ID do paciente logado
        paciente_id = self.manager.app.logged_user_id
        # Pega o código digitado
        codigo = self.ids.vincula_input.text.strip()

        # Validação simples
        if not paciente_id:
            self.show_popup("Erro", "Não foi possível identificar o seu login. Tente novamente.")
            return
        if not codigo:
            self.show_popup("Erro", "Por favor, digite o código de convite.")
            return

        # Pega a instância do banco de dados
        db = self.manager.app.db
        
        # Chama a nova função da base de dados
        success, msg = db.vincular_paciente_por_codigo(paciente_id, codigo)

        if success:
            self.show_popup("Sucesso!", msg)
            self.ids.vincula_input.text = "" # Limpa o campo
            # Opcional: Esconder o card de vincular
            self.ids.vincula_card.height = "0dp"
            self.ids.vincula_card.opacity = 0
            self.ids.vincula_card.disabled = True
        else:
            self.show_popup("Erro", msg)

    # --- Funções de Pop-up (KivyMD 2.0.0) ---
    def show_popup(self, title, message):
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogSupportingText(text=message),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="OK"),
                    style="text",
                    on_release=self.close_dialog,
                ),
                spacing="8dp"
            ),
            auto_dismiss=False
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def check_new_notifications(self):
        """Verifica se há mensagens não lidas para mudar o ícone."""
        try:
            db = self.manager.app.db
            user_id = self.manager.app.logged_user_id
            
            # Pega todas as notificações
            notificacoes = db.get_minhas_notificacoes(user_id)
            
            # Verifica se existe alguma onde 'lida' é False
            # A API retorna dict: {'lida': False, ...}
            tem_novas = any(n['lida'] is False for n in notificacoes)
            
            botao = self.ids.btn_notificacao
            if tem_novas:
                botao.icon = "bell-badge" # Ícone com bolinha
                botao.icon_color = [1, 0, 0, 1] # Vermelho (Destaque)
            else:
                botao.icon = "bell-outline" # Ícone normal
                botao.icon_color = [1, 1, 1, 1] # Branco
                
        except Exception as e:
            print(f"Erro ao checar notificações: {e}")

class AgendamentoScreen(Screen):
    def on_enter(self):
        self.carregar_horarios()

    def carregar_horarios(self):
        container = self.ids.container_horarios
        container.clear_widgets()
        
        db = self.manager.app.db
        paciente_id = self.manager.app.logged_user_id
        
        psicologo_id = db.get_psicologo_id_by_paciente(paciente_id) 
        
        if not psicologo_id:
            container.add_widget(MDLabel(text="Você ainda não tem psicólogo vinculado.", halign="center"))
            return

        horarios = db.get_horarios_disponiveis(psicologo_id)
        
        if not horarios:
            container.add_widget(MDLabel(text="Sem horários disponíveis no momento.", halign="center"))
            return

        # Loop com o ajuste do Unpack (ag_id, data_texto, _)
        for ag_id, data_texto, _ in horarios:
            
            # 1. Converte Texto da API -> Objeto Data
            try:
                dt_obj = datetime.fromisoformat(data_texto)
            except ValueError:
                dt_obj = datetime.strptime(data_texto, "%Y-%m-%d %H:%M:%S")
            
            # 2. Converte Objeto Data -> Texto Bonito para Exibir (STRING)
            data_fmt = dt_obj.strftime("%d/%m - %H:%M") 

            card = MDCard(
                style="elevated",
                size_hint_y=None,
                height="80dp",
                padding="15dp",
                ripple_behavior=True,
                on_release=lambda x, i=ag_id, d=data_fmt: self.confirmar_agendamento(i, d)
            )
            
            layout = MDBoxLayout(orientation="horizontal")
            layout.add_widget(MDIcon(icon="calendar-check", pos_hint={"center_y": .5}))
            
            # --- CORREÇÃO AQUI ---
            # Use 'data_fmt' (que é string), NUNCA use 'dt_obj' ou 'data_texto' direto se não for string
            layout.add_widget(MDLabel(
                text=data_fmt,  # <--- ISSO DEVE SER STRING
                font_style="Title", 
                role="medium", 
                pos_hint={"center_y": .5}, 
                padding=[20,0,0,0]
            ))
            
            card.add_widget(layout)
            container.add_widget(card)

    def confirmar_agendamento(self, agenda_id, data_texto):
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Confirmar Agendamento"),
            MDDialogSupportingText(text=f"Deseja marcar consulta para {data_texto}?"),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancelar"), on_release=lambda x: self.dialog.dismiss()),
                MDButton(MDButtonText(text="Confirmar"), on_release=lambda x: self.finalizar_agendamento(agenda_id))
            )
        )
        self.dialog.open()

    def finalizar_agendamento(self, agenda_id):
        db = self.manager.app.db
        paciente_id = self.manager.app.logged_user_id
        
        success, msg = db.agendar_consulta(agenda_id, paciente_id)
        
        self.dialog.dismiss()
        # Feedback visual simples (pode ser um dialog de sucesso)
        print(msg) 
        if success:
            self.manager.current = "home" # Volta pra home após agendar

class NotificationScreen(Screen):
    dialog = None # Inicializa variável do dialog

    def on_enter(self):
        self.carregar_notificacoes()

    def carregar_notificacoes(self):
        container = self.ids.container_notificacoes
        container.clear_widgets()

        # ACESSO CORRETO AO BANCO DE DADOS
        app = MDApp.get_running_app() # Forma segura de pegar o app
        db = app.db
        user_id = app.logged_user_id
        
        # 1. Busca e marca como lidas
        notificacoes = db.get_minhas_notificacoes(user_id)
        
        # Marca como lida apenas se tiver alguma não lida
        tem_nao_lida = any(not n['lida'] for n in notificacoes)
        if tem_nao_lida:
            db.marcar_notificacoes_lidas(user_id)

        if not notificacoes:
            container.add_widget(MDLabel(text="Nenhuma notificação.", halign="center", pos_hint={"center_y": .5}))
            return

        for n in notificacoes:
            # ... (O resto do seu código de criar MDListItem está perfeito) ...
            # Mantenha exatamente como você fez:
            n_id = n['id']
            icon_name = "email-open" if n['lida'] else "email-alert"
            icon_color = [0.5, 0.5, 0.5, 1] if n['lida'] else [0.29, 0.62, 0.22, 1]
            
            item = MDListItem(
                MDListItemLeadingIcon(
                    icon=icon_name, 
                    theme_icon_color="Custom",
                    icon_color=icon_color
                ),
                MDListItemHeadlineText(text=n['titulo']),
                MDListItemSupportingText(text=n['mensagem']),
                radius=[15],
                theme_bg_color="Custom",
                md_bg_color=[1, 1, 1, 1],
                ripple_effect=True,
                on_release=lambda x, t=n['titulo'], m=n['mensagem']: self.ver_detalhes(t, m)
            )
            
            btn_del = MDIconButton(
                icon="close",
                pos_hint={"center_y": .5},
                on_release=lambda x, i=n_id: self.deletar(i)
            )
            item.add_widget(btn_del)
            container.add_widget(item)

    def ver_detalhes(self, titulo, mensagem):
        """Abre um pop-up com a mensagem completa e opção de copiar."""
        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            MDDialogHeadlineText(text=titulo),
            MDDialogSupportingText(text=mensagem), # Aqui aparece o texto inteiro!
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Fechar"), 
                    style="text", 
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDButton(
                    MDButtonText(text="Copiar"), 
                    style="filled", 
                    theme_bg_color="Custom",
                    md_bg_color=[0.57, 0.78, 0.64, 1], # Verde do tema
                    on_release=lambda x: self.copiar_codigo(mensagem)
                ),
                spacing="8dp",
            ),
        )
        self.dialog.open()

    def copiar_codigo(self, texto):
        """Procura o código dentro do texto e copia."""
        # Regex para achar o padrão: "código... é: XXX-XXX"
        # Procura qualquer coisa que pareça um código após "é: "
        match = re.search(r"é:\s*([A-Z0-9-]+)", texto)
        
        if match:
            codigo = match.group(1)
            Clipboard.copy(codigo) # Copia para o Ctrl+V do celular/PC
            #print(f"Copiado: {codigo}")
            self.dialog.dismiss()
            self.show_aviso("Sucesso", f"Código {codigo} copiado!")
        else:
            # Se não achar o padrão, copia o texto todo por segurança
            Clipboard.copy(texto)
            self.dialog.dismiss()
            self.show_aviso("Copiado", "Mensagem completa copiada.")

    def deletar(self, notif_id):
        db = self.manager.app.db
        if db.deletar_notificacao(notif_id):
            self.carregar_notificacoes()

    def show_aviso(self, titulo, msg):
        # Pop-up simples de feedback
        self.aviso = MDDialog(
            MDDialogHeadlineText(text=titulo),
            MDDialogSupportingText(text=msg),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="OK"), on_release=lambda x: self.aviso.dismiss())
            )
        )
        self.aviso.open()