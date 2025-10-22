from kivy.uix.screenmanager import Screen
from datetime import date
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton

class RegisterActivityScreen(Screen):
        dialog = None

        # Este é o seu dicionário (a "ponte")
        chip_map = {
            "chk_fisicas": "Pratiquei atividades físicas",
            "chk_mercado": "Fui ao Mercado",
            "chk_bebidas": "Consumi bebidas alcoólicas",
            "chk_estudei": "Estudei",
            "chk_meditei": "Meditei",
            "chk_musicas": "Ouvi Músicas",
            "chk_desenhei": "Desenhei, pintei ou colori",
            "chk_aprendi": "Aprendi algo novo (ex: idioma)",
            "chk_amigo": "Encontrei um amigo ou familiar"

        }

        def do_register_activities(self):
            """
            Coleta todas as atividades selecionadas e as salva no banco de dados.
            """
            atividades_selecionadas = []

            # 1. Lê os chips e constrói a lista de strings (Valores)
            for chip_id, texto_atividade in self.chip_map.items():
                if self.ids[chip_id].active:
                    atividades_selecionadas.append(texto_atividade)

            # 2. Verifica se algo foi selecionado
            if not atividades_selecionadas:
                self.show_popup("Atenção", "Você não selecionou nenhuma atividade.")
                return

            # 3. Tenta salvar no banco de dados
            try:
                # Pega o ID do utilizador e o banco de dados da app principal
                user_id = self.manager.app.logged_user_id
                db = self.manager.app.db
                hoje = date.today().isoformat()  # Ex: "2025-10-21"

                # Chama a nova função do database
                success, msg = db.add_atividades_diarias(user_id, atividades_selecionadas, hoje)
                print(success, msg)
                if success:
                    self.show_popup("Sucesso", "Suas atividades foram registradas!")
                    # Opcional: voltar para a tela home
                    self.manager.current = 'home'
                    atividades_selecionadas.clear()
                else:
                    self.show_popup("Erro", msg)

            except Exception as e:
                print(f"Erro ao tentar registrar atividades: {e}")
                self.show_popup("Erro", "Não foi possível salvar. Verifique se está logado.")

        def show_popup(self, title, message):
            if self.dialog:
                self.dialog.dismiss()
            close_button = MDFlatButton(
                text="OK",
                on_release=self.close_dialog
            )
            self.dialog = MDDialog(
                title=title,
                text=message,
                buttons=[close_button]
            )
            self.dialog.open()

        def close_dialog(self, *args):
            if self.dialog:
                self.dialog.dismiss()