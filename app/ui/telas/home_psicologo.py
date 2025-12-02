import threading
import webbrowser
import base64
from io import BytesIO
from kivy.core.image import Image as CoreImage
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from datetime import datetime

from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
    MDDialogContentContainer
)
from kivymd.uix.textfield import (
    MDTextField,
    MDTextFieldLeadingIcon,
    MDTextFieldHintText,
)
from kivymd.uix.list import (
    MDListItem, 
    MDListItemLeadingIcon, 
    MDListItemHeadlineText, 
    MDListItemSupportingText
)
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.label import MDLabel
from kivy.properties import StringProperty

class PsychoHomeScreen(MDScreen):
    dialog = None 
    loading_dialog = None 
    email_dialog = None 

    def on_enter(self, *args):
        """Chamado sempre que a tela é exibida."""
        self.load_user_data()
        self.load_dashboard_data()

    def load_user_data(self):
        """Carrega o NOME e ID do psicólogo logado."""
        try:
            # Verifica se o ID e Nome estão disponíveis na App class
            if hasattr(self.manager.app, 'logged_user_name'):
                username = self.manager.app.logged_user_name
                self.ids.id_label.text = f"Bem-vindo(a), {username}"
            else:
                self.ids.id_label.text = "Bem-vindo(a), Doutor(a)"
            
        except Exception as e:
            print(f"Erro ao carregar dados do psicólogo: {e}")
            self.ids.id_label.text = "Bem-vindo"

    def load_dashboard_data(self):
        """Inicia thread para atualizar cards."""
        # Define textos de "carregando..." na propriedade 'subtitle' dos cards
        self.ids.patient_summary_card.subtitle = "Contando pacientes..."
        
        try:
            psicologo_id = self.manager.app.logged_user_id
            threading.Thread(
                target=self._thread_load_dashboard,
                args=(psicologo_id,),
                daemon=True
            ).start()
        except Exception as e:
            print(f"Erro ao iniciar thread: {e}")

    def _thread_load_dashboard(self, psicologo_id):
        try:
            db = self.manager.app.db
            
            # 1. Busca contagem
            success_count, count = db.get_patient_count(psicologo_id)
            print(f"[DEBUG] Success: {success_count}, Count: {count}") # <--- DEBUG

            # 2. Busca próxima consulta
            success_appt, next_appt = db.get_next_appointment(psicologo_id)

            # Prepara os textos
            if success_count:
                texto_pacientes = f"{count} pacientes vinculados"
            else:
                texto_pacientes = "Erro ao contar"

            data_ui = {
                'count_text': texto_pacientes,
                'appt_text': "Nenhuma consulta agendada"
            }

            # Lógica da próxima consulta (Mantém igual)
            if success_appt and next_appt:
                data_iso, paciente_nome = next_appt
                try:
                    data_limpa = str(data_iso).replace('Z', '')
                    if 'T' in data_limpa:
                        dt = datetime.fromisoformat(data_limpa)
                    else:
                        dt = datetime.strptime(data_limpa, "%Y-%m-%d %H:%M:%S")
                    data_formatada = dt.strftime("%d/%m às %H:%M")
                    data_ui['appt_text'] = f"{data_formatada} - {paciente_nome}"
                except Exception as e:
                    data_ui['appt_text'] = f"{data_iso} - {paciente_nome}"
            
            # Atualiza a UI
            Clock.schedule_once(lambda dt: self._update_dashboard_ui(data_ui))
            
        except Exception as e:
            print(f"Erro na thread dashboard: {e}")

    def _update_dashboard_ui(self, data_ui):
        # Garante que os IDs existem antes de tentar atualizar
        if hasattr(self.ids, 'patient_summary_card'):
            self.ids.patient_summary_card.subtitle = data_ui['count_text']
        if hasattr(self.ids, 'next_appointment_card'):
            self.ids.next_appointment_card.subtitle = data_ui['appt_text']

    def navigate_to(self, screen_name):
        self.manager.current = screen_name

    # --- Lógica de E-mail (Mantida igual) ---
    def show_email_dialog(self):
        self.email_input = MDTextField(
            MDTextFieldLeadingIcon(icon="email-outline"),
            MDTextFieldHintText(text="E-mail do paciente"),
        )
        self.email_dialog = MDDialog(
            MDDialogHeadlineText(text="Enviar convite"),
            MDDialogContentContainer(self.email_input),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancelar"),
                    style="text",
                    on_release=self.close_dialog
                ),
                MDButton(
                    MDButtonText(text="Enviar"),
                    style="text",
                    on_release=self.iniciar_envio_email
                ),
                spacing="8dp",
            ),
        )
        self.email_dialog.open()

    def iniciar_envio_email(self, *args):
        paciente_email = self.email_input.text.strip()
        if not paciente_email or "@" not in paciente_email:
            self.show_ok_dialog("Erro", "E-mail inválido.")
            return
        
        psicologo_id = self.manager.app.logged_user_id
        self.close_dialog()
        self.show_loading_dialog("Enviando...")
        
        # Roda em thread para não travar a tela
        threading.Thread(target=self._processar_envio, args=(psicologo_id, paciente_email)).start()

    def _processar_envio(self, uid, email):
        db = self.manager.app.db
        # Chama a API
        success, msg = db.enviar_convite(uid, email)
        
        # Volta para a UI
        Clock.schedule_once(lambda dt: self._pos_envio(msg))

    def _pos_envio(self, msg):
        self.dismiss_loading_dialog()
        self.show_ok_dialog("Aviso", msg)


    def show_add_activity_dialog(self):
        # Campo de texto para o nome da atividade
        self.activity_input = MDTextField(
            MDTextFieldHintText(text="Nome da atividade (ex: Yoga)"),
            mode="outlined",
        )

        # Botões Cancelar e Salvar
        cancel_btn = MDButton(
            MDButtonText(text="Cancelar"),
            style="text",
            on_release=self.close_add_dialog
        )
        save_btn = MDButton(
            MDButtonText(text="Salvar"),
            style="text",
            on_release=self.salvar_nova_atividade
        )

        self.add_activity_dialog = MDDialog(
            MDDialogHeadlineText(text="Nova Atividade"),
            MDDialogSupportingText(text="Adicione uma atividade que ficará visível para os pacientes."),
            MDDialogContentContainer(
                self.activity_input,
                orientation="vertical"
            ),
            MDDialogButtonContainer(
                cancel_btn,
                save_btn,
                spacing="8dp",
            ),
        )
        self.add_activity_dialog.open()

    def close_add_dialog(self, *args):
        if self.add_activity_dialog:
            self.add_activity_dialog.dismiss()
            self.add_activity_dialog = None

    def salvar_nova_atividade(self, *args):
        texto_atividade = self.activity_input.text.strip()
        
        if not texto_atividade:
            self.show_ok_dialog("Erro", "O nome da atividade não pode ser vazio.")
            return

        try:
            db = self.manager.app.db
            # Chama a função do banco (veja o passo 3 abaixo)
            success, msg = db.adicionar_atividade_template(texto_atividade)

            self.close_add_dialog() # Fecha o diálogo de input

            if success:
                self.show_ok_dialog("Sucesso", f"Atividade '{texto_atividade}' criada!")
            else:
                self.show_ok_dialog("Erro", msg)

        except Exception as e:
            print(f"Erro ao salvar atividade: {e}")
            self.show_ok_dialog("Erro", "Falha interna ao salvar.")

    def show_loading_dialog(self, text="Aguarde..."):
        if self.loading_dialog: self.loading_dialog.dismiss()
        spinner = MDCircularProgressIndicator(size_hint=(None, None), size=("40dp", "40dp"))
        content = MDDialogContentContainer(spinner, orientation="vertical")
        self.loading_dialog = MDDialog(content, auto_dismiss=False)
        self.loading_dialog.open()

    def dismiss_loading_dialog(self):
        if self.loading_dialog: self.loading_dialog.dismiss()

    def show_ok_dialog(self, title, message):
        if self.dialog: self.dialog.dismiss()
        btn = MDButton(MDButtonText(text="OK"), style="text", on_release=self.close_dialog)
        self.dialog = MDDialog(
            MDDialogHeadlineText(text=title), 
            MDDialogSupportingText(text=message), 
            MDDialogButtonContainer(btn)
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog: self.dialog.dismiss()
        if self.email_dialog: self.email_dialog.dismiss()


class PatientListScreen(MDScreen):
    def on_enter(self, *args):
        Clock.schedule_once(self.load_patients)

    def load_patients(self, *args):
        list_widget = self.ids.patient_list_container
        list_widget.clear_widgets()
        
        try:
            db = self.manager.app.db
            psicologo_id = self.manager.app.logged_user_id
            pacientes = db.get_pacientes_do_psicologo(psicologo_id)

            if not pacientes:
                # Cria um label simples se não tiver pacientes
                lbl = MDLabel(
                    text="Nenhum paciente vinculado.", 
                    halign="center", 
                    theme_text_color="Secondary"
                )
                list_widget.add_widget(lbl)
                return

            for paciente_id, nome_paciente in pacientes:
                # --- AQUI ESTAVA O PROBLEMA ---
                # Criamos o item da lista de forma limpa
                item = MDListItem(
                    MDListItemLeadingIcon(
                        icon="account-circle",
                        theme_icon_color="Custom",
                        icon_color=[0.57, 0.78, 0.64, 1] # Verde do tema
                    ),
                    MDListItemHeadlineText(text=nome_paciente),
                    MDListItemSupportingText(text=f"ID: {paciente_id}"),
                    
                    # Propriedades visuais seguras
                    # radius=[15], # Comente se der erro de lista/float
                    theme_bg_color="Custom",
                    md_bg_color=[1, 1, 1, 1], # Branco
                    ripple_effect=True, # Efeito de clique
                    
                    # Evento de clique (Lambda correto)
                    on_release=lambda x, pid=paciente_id, pname=nome_paciente: self.view_patient_details(pid, pname)
                )
                
                list_widget.add_widget(item)

        except Exception as e:
            print(f"Erro lista pacientes: {e}")
            list_widget.add_widget(MDLabel(text="Erro ao carregar lista.", halign="center"))

    def view_patient_details(self, paciente_id, nome_paciente):
        """
        Ao clicar no paciente, salva o ID na App e vai para a tela de relatório.
        """
        print(f"Abrindo relatório para: {nome_paciente}")
        
        # 1. Salva o ID no app para a outra tela usar
        # Criamos variáveis novas no app para não misturar com o diário
        self.manager.app.paciente_em_analise_id = paciente_id
        self.manager.app.paciente_em_analise_nome = nome_paciente
        
        # 2. Navega para a tela de relatório (que criamos abaixo)
        self.manager.current = "relatorio_paciente"

class RelatorioPacienteScreen(MDScreen):
    def on_enter(self):
        # Pega o ID salvo
        if hasattr(self.manager.app, 'paciente_em_analise_id'):
            paciente_id = self.manager.app.paciente_em_analise_id
            nome = getattr(self.manager.app, 'paciente_em_analise_nome', 'Paciente')
            self.ids.titulo_header.text = f"Relatório: {nome}"
            
            self.limpar_tela()
            self.carregar_dados(paciente_id)

    def limpar_tela(self):
        self.ids.img_evolucao.texture = None
        self.ids.img_distribuicao.texture = None
        self.ids.lbl_resumo.text = "Carregando análise..."

    def carregar_dados(self, paciente_id):
        # Thread para não travar o app enquanto baixa as imagens
        threading.Thread(target=self._fetch_data_thread, args=(paciente_id,), daemon=True).start()

    def _fetch_data_thread(self, pid):
        try:
            import requests
            
            # --- CORREÇÃO FINAL DA CONEXÃO ---
            # Aqui é o pulo do gato: Em vez de tentar adivinhar a URL, 
            # pegamos EXATAMENTE a mesma URL que o arquivo 'neon.py' está usando.
            # Se neon.py estiver localhost, usa localhost. Se estiver Render, usa Render.
            
            base_url = "http://127.0.0.1:8000" # Fallback
            
            if hasattr(self.manager.app, 'db') and hasattr(self.manager.app.db, 'base_url'):
                 base_url = self.manager.app.db.base_url
            
            # Garante a barra no final
            if not base_url.endswith('/'):
                base_url += '/'
            
            # Monta URL completa
            full_url = f"{base_url}relatorios/analise/{pid}"
            
            resp = requests.get(full_url)
            
            if resp.status_code == 200:
                data = resp.json()
                Clock.schedule_once(lambda dt: self._update_ui(data))
            else:
                msg_erro = f"Erro {resp.status_code}: {resp.text}"
                Clock.schedule_once(lambda dt: self._show_error(msg_erro))
                
        except Exception as e:
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self._show_error(err_msg))

    def _update_ui(self, data):
        # 1. Atualiza Texto
        self.ids.lbl_resumo.text = data['resumo_texto']

        # 2. Atualiza Gráficos
        if data.get('grafico_evolucao_base64'):
            self.aplicar_grafico(self.ids.img_evolucao, data['grafico_evolucao_base64'])
            
        if data.get('grafico_distribuicao_base64'):
            self.aplicar_grafico(self.ids.img_distribuicao, data['grafico_distribuicao_base64'])

    def _show_error(self, msg):
        self.ids.lbl_resumo.text = f"Não foi possível gerar o relatório.\n{msg}"

    def aplicar_grafico(self, image_widget, base64_string):
        try:
            # Decodifica string Base64 para binário
            data = base64.b64decode(base64_string)
            data_io = BytesIO(data)
            
            # Cria textura Kivy
            im = CoreImage(data_io, ext='png')
            
            # Aplica no widget
            image_widget.texture = im.texture
        except Exception as e:
            print(f"Erro ao renderizar imagem: {e}")
            
    def view_patient_details_powerBI(self):
        """
        Abre o navegador padrão com o Dashboard do Power BI.
        """
        
        # 1. Coloque aqui o seu Link Público ou Privado do Power BI
        url_base = "https://app.powerbi.com/view?r=eyJrIjoiYzZkOTBiZWYtMzNkOC00OTczLWE5YzQtMTI5NGY2ODU5MzQ4IiwidCI6ImRlZjQ0ZjhmLWFlM2EtNDA4MS1iY2EzLWYwODBhZDkzYTUxYyJ9"
        
        # (OPCIONAL) Filtrar pelo paciente específico
        # Se o seu relatório tiver uma tabela 'Pacientes' com coluna 'ID', você pode filtrar na URL:
        # url_final = f"{url_base}&filter=Pacientes/ID eq {paciente_id}"
        
        # Por enquanto, vamos abrir o link direto:
        webbrowser.open(url_base)

# Classe customizada para o item da lista (suporta eventos de editar/excluir)
class ActivityListItem(MDListItem):
    text = StringProperty()
    
    def on_edit(self):
        # Chama a função de editar na tela pai
        self.parent_screen.show_edit_dialog(self.atividade_id, self.text)


    def on_delete(self):
        # Chama a função de excluir na tela pai
        self.parent_screen.show_delete_confirmation(self.atividade_id, self.text)


class ListAtividadeScreen(MDScreen):
    dialog = None
    def on_enter(self):
        self.carregar_atividades()

    def carregar_atividades(self):
        list_widget = self.ids.lista_selecao_atividades
        list_widget.clear_widgets()
        db = self.manager.app.db
        success, atividades = db.get_atividades_template()
        
        if success and atividades:
            for ativ_id, nome in atividades:
                item = ActivityListItem()
                item.text = nome
                item.atividade_id = ativ_id
                item.parent_screen = self
                list_widget.add_widget(item)

    def show_add_dialog(self):
        self.input_field = MDTextField(MDTextFieldHintText(text="Nome da atividade"), mode="outlined")
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Nova Atividade"),
            MDDialogContentContainer(self.input_field),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancelar"), on_release=lambda x: self.dialog.dismiss()),
                MDButton(MDButtonText(text="Salvar"), on_release=self.salvar_nova)
            )
        )
        self.dialog.open()

    def salvar_nova(self, *args):
        texto = self.input_field.text.strip()
        if texto:
            db = self.manager.app.db
            psicologo_id = self.manager.app.logged_user_id
            db.adicionar_atividade_template(texto, psicologo_id)
            self.carregar_atividades()
        self.dialog.dismiss()

    # --- EDITAR ---
    def show_edit_dialog(self, ativ_id, texto_atual):
        self.edit_input = MDTextField(
            MDTextFieldHintText(text="Editar nome"),
            text=texto_atual,
            mode="outlined"
        )
        
        # Usando lambda para passar o ID para a função de salvar
        save_callback = lambda x: self.salvar_edicao(ativ_id)
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Editar Atividade"),
            MDDialogContentContainer(self.edit_input),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancelar"), style="text", on_release=self.close_dialog),
                MDButton(MDButtonText(text="Atualizar"), style="text", on_release=save_callback),
                spacing="8dp"
            )
        )
        self.dialog.open()

    def salvar_edicao(self, ativ_id):
        novo_texto = self.edit_input.text.strip()
        if novo_texto:
            # --- CÓDIGO REAL ---
            db = self.manager.app.db
            success, msg = db.update_atividade_template(ativ_id, novo_texto)
            
            if success:
                self.carregar_atividades() # Atualiza a lista na tela
            else:
                print(msg) # (Opcional) Mostre um pop-up de erro aqui se quiser
                
        self.close_dialog()

    # --- EXCLUIR ---
    def show_delete_confirmation(self, ativ_id, nome_ativ):
        delete_callback = lambda x: self.confirmar_exclusao(ativ_id)
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Excluir Atividade?"),
            MDDialogSupportingText(text=f"Tem certeza que deseja remover '{nome_ativ}'?"),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Não"), style="text", on_release=self.close_dialog),
                MDButton(MDButtonText(text="Sim, Excluir"), style="text", theme_text_color="Error", on_release=delete_callback),
                spacing="8dp"
            )
        )
        self.dialog.open()

    def confirmar_exclusao(self, ativ_id):
        # --- CÓDIGO REAL ---
        db = self.manager.app.db
        success, msg = db.delete_atividade_template(ativ_id)
        
        if success:
            self.carregar_atividades() # Remove o item da tela
        else:
            # Mostra erro se tentar apagar algo que já foi usado
            # Recomendo criar um dialog simples aqui, mas o print serve para teste
            print(f"Erro: {msg}") 
            
        self.close_dialog()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

class DisponibilidadeScreen(MDScreen):
    def on_enter(self):
        self.carregar_agenda()

    def carregar_agenda(self):
        # Limpa as duas listas
        container_agendados = self.ids.lista_agendados
        container_livres = self.ids.lista_livres
        
        container_agendados.clear_widgets()
        container_livres.clear_widgets()
        
        db = self.manager.app.db
        psicologo_id = self.manager.app.logged_user_id
        
        # Busca tudo do banco
        todos_horarios = db.get_agenda_psicologo(psicologo_id)

        if not todos_horarios:
            container_livres.add_widget(MDLabel(text="Nenhum horário cadastrado.", halign="center"))
            return

        # Separa em duas listas python
        # Estrutura: (id, data, paciente_id)
        lista_agendados = [h for h in todos_horarios if h[2] is not None]
        lista_livres = [h for h in todos_horarios if h[2] is None]

        # --- PREENCHE AGENDADOS ---
        if not lista_agendados:
            container_agendados.add_widget(MDLabel(text="Nenhuma consulta marcada.", theme_text_color="Secondary", font_style="Label", role="medium"))
        
        for ag_id, data_hora_texto, pac_id in lista_agendados:
            data_fmt, hora_fmt = self._formatar_data(data_hora_texto)
            
            item = MDListItem(
                MDListItemLeadingIcon(icon="calendar-check", theme_icon_color="Custom", icon_color=[0, 0.5, 0, 1]), # Ícone verde check
                MDListItemHeadlineText(text=f"{data_fmt} às {hora_fmt}"),
                MDListItemSupportingText(text=f"Paciente ID: {pac_id}", theme_text_color="Error"),
                theme_bg_color="Custom",
                md_bg_color=[1, 1, 1, 1],
                radius=[10],
            )
            # Botão Cancelar (Lixeira)
            btn_delete = MDIconButton(
                icon="close-circle-outline",
                style="standard",
                theme_icon_color="Custom",
                icon_color=[1, 0, 0, 1],
                pos_hint={"center_y": .5},
                on_release=lambda x, i=ag_id: self.excluir_horario(i)
            )
            item.add_widget(btn_delete)
            container_agendados.add_widget(item)

        # --- PREENCHE LIVRES ---
        for ag_id, data_hora_texto, pac_id in lista_livres:
            data_fmt, hora_fmt = self._formatar_data(data_hora_texto)
            
            item = MDListItem(
                MDListItemLeadingIcon(icon="clock-outline"),
                MDListItemHeadlineText(text=f"{data_fmt} às {hora_fmt}"),
                MDListItemSupportingText(text="Disponível"),
                theme_bg_color="Custom",
                md_bg_color=[1, 1, 1, 1],
                radius=[10],
            )
            # Botão Excluir
            btn_delete = MDIconButton(
                icon="trash-can-outline",
                style="standard",
                theme_icon_color="Custom",
                icon_color=[0.5, 0.5, 0.5, 1], # Cinza para horários livres
                pos_hint={"center_y": .5},
                on_release=lambda x, i=ag_id: self.excluir_horario(i)
            )
            item.add_widget(btn_delete)
            container_livres.add_widget(item)

    def _formatar_data(self, data_texto):
        """Helper para formatar a data sem repetir código"""
        try:
            dt_obj = datetime.fromisoformat(data_texto)
        except ValueError:
            try:
                dt_obj = datetime.strptime(data_texto, "%Y-%m-%d %H:%M:%S")
            except:
                return data_texto, ""
        
        return dt_obj.strftime("%d/%m/%Y"), dt_obj.strftime("%H:%M")

    def adicionar_horario_dialog(self):
        self.data_input = MDTextField(MDTextFieldHintText(text="Data (DD/MM/AAAA)"), mode="outlined")
        self.hora_input = MDTextField(MDTextFieldHintText(text="Hora (HH:MM)"), mode="outlined")
        
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Novo Horário"),
            MDDialogContentContainer(self.data_input, self.hora_input, orientation="vertical", spacing="10dp"),
            MDDialogButtonContainer(
                MDButton(MDButtonText(text="Cancelar"), on_release=lambda x: self.dialog.dismiss()),
                MDButton(MDButtonText(text="Salvar"), on_release=self.salvar_horario)
            )
        )
        self.dialog.open()

    def salvar_horario(self, *args):
        try:
            dt_obj = datetime.strptime(f"{self.data_input.text} {self.hora_input.text}", "%d/%m/%Y %H:%M")
            db = self.manager.app.db
            psicologo_id = self.manager.app.logged_user_id
            
            if db.adicionar_disponibilidade(psicologo_id, dt_obj):
                self.carregar_agenda()
                self.dialog.dismiss()
        except ValueError:
            print("Data inválida")

    def excluir_horario(self, agenda_id):
        db = self.manager.app.db
        if db.excluir_horario(agenda_id):
            self.carregar_agenda()