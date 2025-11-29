import requests
import json

class Database:
    def __init__(self):
        # Em desenvolvimento use localhost. Em produção use a URL do Render.
        #self.base_url = "http://127.0.0.1:8000" # Conexão local
        #self.base_url = "https://api-tcc-cognitive.onrender.com"   # Conexão com Render
        self.base_url = "https://api-tcc-cognitive.vercel.app/"    # Conexão com a Vercel

    # --- AUTH ---
    def register_user(self, username, password, user_type, email, data_nascimento_str):
        url = f"{self.base_url}/register"
        payload = {
            "username": username, "password": password, 
            "user_type": user_type, "email": email, 
            "data_nascimento": data_nascimento_str
        }
        try:
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                return True, "Registrado com sucesso!", res.json().get("id")
            else:
                return False, res.json().get("detail", "Erro"), None
        except Exception as e:
            return False, str(e), None

    def verify_user(self, email, password):
        url = f"{self.base_url}/login"
        try:
            res = requests.post(url, json={"email": email, "password": password})
            if res.status_code == 200:
                d = res.json()
                return True, "Login OK", d['user_type'], d['id'], d['username']
            return False, res.json().get("detail", "Erro"), None, None
        except:
            return False, "Erro de conexão", None, None

    # --- PSICÓLOGO ---
    def get_patient_count(self, psicologo_id):
        try:
            res = requests.get(f"{self.base_url}/psicologo/{psicologo_id}/stats")
            if res.status_code == 200:
                return True, res.json()['pacientes_count']
            return False, 0
        except: return False, 0

    def get_next_appointment(self, psicologo_id):
        try:
            res = requests.get(f"{self.base_url}/psicologo/{psicologo_id}/stats")
            if res.status_code == 200:
                data = res.json()['proxima_consulta'] # Retorna lista [data, nome] ou None
                return True, tuple(data) if data else None
            return False, None
        except: return False, None

    def get_pacientes_do_psicologo(self, psicologo_id):
        try:
            res = requests.get(f"{self.base_url}/psicologo/{psicologo_id}/pacientes")
            if res.status_code == 200:
                # API retorna lista de listas [[1, "joao"]], convertemos para lista de tuplas
                return [tuple(x) for x in res.json()['pacientes']]
            return []
        except: return []

    # --- ATIVIDADES ---
    def get_atividades_template(self):
        try:
            res = requests.get(f"{self.base_url}/atividades")
            if res.status_code == 200:
                return True, [tuple(x) for x in res.json()['atividades']]
            return False, []
        except: return False, []

    def adicionar_atividade_template(self, texto, psicologo_id):
        try:
            res = requests.post(f"{self.base_url}/atividades", json={"texto": texto, "psicologo_id": psicologo_id})
            if res.status_code == 200:
                return True, "Criado com sucesso"
            return False, res.json().get("detail")
        except Exception as e: return False, str(e)

    def delete_atividade_template(self, atividade_id):
        try:
            res = requests.delete(f"{self.base_url}/atividades/{atividade_id}")
            if res.status_code == 200: return True, "Excluído"
            return False, res.json().get("detail")
        except Exception as e: return False, str(e)

    def update_atividade_template(self, atividade_id, novo_texto):
        try:
            res = requests.put(f"{self.base_url}/atividades/{atividade_id}?novo_texto={novo_texto}")
            if res.status_code == 200: return True, "Atualizado"
            return False, res.json().get("detail")
        except: return False, "Erro"

    # --- DIÁRIO ---
    def add_entrada_completa_diario(self, user_id, data_hora, sentimento_id, anotacao, atividades_ids):
        url = f"{self.base_url}/diario"
        payload = {
            "paciente_id": user_id,
            "data_hora_iso": data_hora,
            "sentimento_id": sentimento_id,
            "anotacao": anotacao,
            "atividades_ids": atividades_ids
        }
        try:
            res = requests.post(url, json=payload)
            if res.status_code == 200: return True, "Salvo!"
            return False, res.json().get("detail")
        except Exception as e: return False, str(e)

    def get_entradas_historico(self, user_id):
        try:
            res = requests.get(f"{self.base_url}/diario/historico/{user_id}")
            if res.status_code == 200:
                return True, [tuple(x) for x in res.json()['historico']]
            return False, []
        except: return False, []
    
    def get_psicologo_id_by_paciente(self, paciente_id):
        """
        Busca qual é o ID do psicólogo vinculado a este paciente via API.
        """
        try:
            url = f"{self.base_url}/paciente/{paciente_id}/psicologo"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                return data.get('psicologo_id') # Retorna o ID (int) ou None
            return None
            
        except Exception as e:
            print(f"[ERRO API] get_psicologo_id_by_paciente: {e}")
            return None
        

    def validar_codigo_master(self, codigo):
        """
        Verifica na API se o código mestre é válido.
        Retorna o ID do código se for válido, ou None se não for.
        """
        try:
            # A rota espera o código na URL
            url = f"{self.base_url}/codigos/master/validar/{codigo}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                if data.get("valid") is True:
                    return data.get("id") # Retorna o ID (ex: 1)
            
            return None # Código inválido ou erro
            
        except Exception as e:
            print(f"[ERRO API] validar_codigo_master: {e}")
            return None

    def marcar_codigo_master_usado(self, codigo_id, user_id):
        """
        Avisa a API para marcar esse código como utilizado por este usuário.
        """
        try:
            url = f"{self.base_url}/codigos/master/usar"
            payload = {"codigo_id": codigo_id, "user_id": user_id}
            
            res = requests.post(url, json=payload)
            return res.status_code == 200
            
        except Exception as e:
            print(f"[ERRO API] marcar_codigo_master_usado: {e}")
            return False
        
    def gerar_codigo_paciente(self, psicologo_id):
        """
        Solicita à API a geração de um novo código de vínculo para paciente.
        Retorna a string do código (ex: "A4B-1C2") ou None se der erro.
        """
        try:
            # A rota na API é: POST /codigos/gerar/{psicologo_id}
            url = f"{self.base_url}/codigos/gerar/{psicologo_id}"
            
            # Enviamos um POST (mesmo sem corpo JSON, a rota exige POST para criar dados)
            res = requests.post(url)
            
            if res.status_code == 200:
                data = res.json()
                return data.get("codigo") # Retorna a string do código
            
            print(f"[API ERRO] gerar_codigo: {res.status_code} - {res.text}")
            return None

        except Exception as e:
            print(f"[ERRO CONEXÃO] gerar_codigo_paciente: {e}")
            return None
        
    def get_pacientes_do_psicologo_com_nomes(self, psicologo_id):
        """
        Retorna uma lista de tuplas (id_paciente, nome_paciente) via API.
        Usado no menu dropdown para selecionar pacientes.
        """
        try:
            # Reutiliza a rota que já criamos na API
            url = f"{self.base_url}/psicologo/{psicologo_id}/pacientes"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                # A API retorna lista de listas: [[1, "Joao"], [2, "Maria"]]
                # O App espera lista de tuplas: [(1, "Joao"), (2, "Maria")]
                return [tuple(x) for x in data.get('pacientes', [])]
            
            return []
            
        except Exception as e:
            print(f"[ERRO API] get_pacientes_do_psicologo_com_nomes: {e}")
            return []
    
    def get_agenda_psicologo(self, psicologo_id):
        """
        Busca a agenda do psicólogo via API.
        Retorna uma lista de tuplas: [(id, data_hora, paciente_id), ...]
        """
        try:
            # Chama a rota GET /agenda/psicologo/{id} que criamos na API
            url = f"{self.base_url}/agenda/psicologo/{psicologo_id}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                # A API retorna {'agenda': [[1, '2023-10...', 5], ...]}
                # Convertemos para lista de tuplas para o Kivy usar
                return [tuple(x) for x in data.get('agenda', [])]
            
            return []
            
        except Exception as e:
            print(f"[ERRO API] get_agenda_psicologo: {e}")
            return []
        
    def get_user_details(self, user_id):
        """
        Busca detalhes do usuário (nome, email, nascimento) via API.
        """
        try:
            url = f"{self.base_url}/users/{user_id}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                
                # Opcional: Converter a data de YYYY-MM-DD para DD/MM/YYYY se seu app precisar
                if data.get('data_nascimento'):
                    try:
                        from datetime import datetime
                        # A API costuma devolver YYYY-MM-DD (ISO)
                        dt = datetime.strptime(data['data_nascimento'], '%Y-%m-%d')
                        data['data_nascimento'] = dt.strftime('%d/%m/%Y')
                    except:
                        pass # Mantém como veio se der erro na conversão
                
                return data
            
            return None

        except Exception as e:
            print(f"[ERRO API] get_user_details: {e}")
            return None
    
    def vincular_paciente_por_codigo(self, paciente_id, codigo):
        """
        Envia o código para a API tentar vincular este paciente a um psicólogo.
        Retorna: (True, "Sucesso") ou (False, "Mensagem de Erro")
        """
        try:
            url = f"{self.base_url}/vincular"
            
            # A rota na API espera um JSON com 'paciente_id' e 'codigo'
            payload = {
                "paciente_id": paciente_id,
                "codigo": codigo
            }
            
            res = requests.post(url, json=payload)
            
            if res.status_code == 200:
                # Se deu certo, retorna sucesso
                return True, "Vínculo realizado com sucesso! Agora seu psicólogo pode ver seus dados."
            
            # Se deu erro (código inválido, já vinculado, etc), pega a mensagem da API
            erro_msg = res.json().get("detail", "Erro desconhecido ao vincular.")
            return False, erro_msg

        except Exception as e:
            print(f"[ERRO API] vincular_paciente_por_codigo: {e}")
            return False, "Falha de conexão com o servidor."
        
    def update_user_details(self, user_id, username, email, data_nascimento):
        """
        Envia os dados atualizados para a API.
        Espera data_nascimento no formato DD/MM/YYYY.
        """
        try:
            url = f"{self.base_url}/users/{user_id}"
            
            payload = {
                "username": username,
                "email": email,
                "data_nascimento": data_nascimento
            }
            
            # Envia requisição PUT
            res = requests.put(url, json=payload)
            
            if res.status_code == 200:
                return True, "Dados atualizados com sucesso!"
            
            # Se der erro (ex: email já existe), pega a mensagem da API
            erro_msg = res.json().get("detail", "Erro ao atualizar.")
            return False, erro_msg

        except Exception as e:
            print(f"[ERRO API] update_user_details: {e}")
            return False, "Erro de conexão."
    
    def adicionar_disponibilidade(self, psicologo_id, data_hora_obj):
        """
        Envia um novo horário de disponibilidade para a API.
        data_hora_obj: objeto datetime (ex: datetime(2023, 10, 25, 14, 30))
        """
        try:
            # A API espera o formato de string ISO 8601
            # Se o argumento já for string, usa direto. Se for datetime, converte.
            if hasattr(data_hora_obj, 'isoformat'):
                data_iso = data_hora_obj.isoformat()
            else:
                data_iso = str(data_hora_obj)

            url = f"{self.base_url}/agenda/disponibilidade"
            
            payload = {
                "psicologo_id": psicologo_id,
                "data_hora_iso": data_iso
            }

            res = requests.post(url, json=payload)

            if res.status_code == 200:
                return True, "Horário adicionado com sucesso!"
            
            # Pega mensagem de erro da API se houver
            erro_msg = res.json().get("detail", "Erro ao salvar horário.")
            return False, erro_msg

        except Exception as e:
            print(f"[ERRO API] adicionar_disponibilidade: {e}")
            return False, "Erro de conexão com o servidor."
        
    def excluir_horario(self, agenda_id):
        """
        Remove um horário da agenda via API.
        """
        try:
            url = f"{self.base_url}/agenda/{agenda_id}"
            res = requests.delete(url)
            
            if res.status_code == 200:
                return True, "Horário removido."
            return False, res.json().get("detail", "Erro ao excluir.")
            
        except Exception as e:
            print(f"[ERRO API] excluir_horario: {e}")
            return False, "Erro de conexão."
        
    def get_horarios_disponiveis(self, psicologo_id):
        """
        Busca a agenda do psicólogo e retorna apenas os horários livres (sem paciente).
        Retorna lista de tuplas: [(id, data_hora_iso, None), ...]
        """
        try:
            # Reutiliza a rota existente da API
            url = f"{self.base_url}/agenda/psicologo/{psicologo_id}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                todos_horarios = data.get('agenda', [])
                
                # Filtra: Mantém apenas se o paciente_id (índice 2) for None
                # A estrutura vinda da API é [id, data_hora, paciente_id]
                disponiveis = [tuple(x) for x in todos_horarios if x[2] is None]
                
                return disponiveis
            
            return []

        except Exception as e:
            print(f"[ERRO API] get_horarios_disponiveis: {e}")
            return []
    
    def reservar_horario(self, agenda_id, paciente_id):
        """
        Reserva um horário específico para o paciente logado.
        """
        try:
            url = f"{self.base_url}/agenda/{agenda_id}/reservar"
            payload = {"paciente_id": paciente_id}
            
            res = requests.put(url, json=payload)
            
            if res.status_code == 200:
                return True, "Agendamento confirmado!"
            
            # Retorna o erro da API (ex: "Horário já reservado")
            msg = res.json().get("detail", "Erro ao agendar.")
            return False, msg
            
        except Exception as e:
            return False, str(e)
        
    def agendar_consulta(self, agenda_id, paciente_id):
        """
        Reserva um horário específico para o paciente logado.
        Chamado pelo botão 'Confirmar' na tela de agendamento.
        """
        try:
            # A rota na API é: PUT /agenda/{id}/reservar
            url = f"{self.base_url}/agenda/{agenda_id}/reservar"
            
            payload = {"paciente_id": paciente_id}
            
            res = requests.put(url, json=payload)
            
            if res.status_code == 200:
                return True, "Agendamento confirmado com sucesso!"
            
            # Pega a mensagem de erro da API (ex: "Horário já ocupado")
            msg = res.json().get("detail", "Erro ao agendar.")
            return False, msg
            
        except Exception as e:
            print(f"[ERRO API] agendar_consulta: {e}")
            return False, "Erro de conexão."

    def get_anotacoes_paciente(self, psicologo_id, paciente_id):
        """
        Busca o histórico de anotações feitas pelo psicólogo sobre este paciente.
        Retorna lista de tuplas: [(id, data, texto), ...]
        """
        try:
            url = f"{self.base_url}/consultas/{psicologo_id}/{paciente_id}"
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()
                # Converte lista de listas para lista de tuplas
                return [tuple(x) for x in data.get('anotacoes', [])]
            
            return []

        except Exception as e:
            print(f"[ERRO API] get_anotacoes_paciente: {e}")
            return []

    def salvar_anotacao_psicologo(self, psicologo_id, paciente_id, texto, data_hora_iso):
        """
        Salva uma nova anotação/relatório de consulta.
        Chamado pela tela 'consulta_anotacao'.
        """
        try:
            # Rota da API que criamos anteriormente (POST /consultas)
            url = f"{self.base_url}/consultas"
            
            payload = {
                "psicologo_id": psicologo_id,
                "paciente_id": paciente_id,
                "anotacao": texto,
                "data_hora_iso": data_hora_iso
            }
            
            res = requests.post(url, json=payload)
            
            if res.status_code == 200:
                return True, "Relatório salvo com sucesso!"
            
            # Tenta pegar a mensagem de erro detalhada da API
            erro_msg = res.json().get("detail", "Erro ao salvar relatório.")
            return False, erro_msg

        except Exception as e:
            print(f"[ERRO API] salvar_anotacao_psicologo: {e}")
            return False, "Erro de conexão com o servidor."

    def enviar_convite(self, psicologo_id, email_paciente):
            """
            Pede para a API gerar um código e enviar por e-mail (Resend).
            """
            try:
                url = f"{self.base_url}/email/enviar_convite"
                payload = {
                    "psicologo_id": psicologo_id,
                    "email_paciente": email_paciente
                }
                
                # Envia a requisição para a API
                res = requests.post(url, json=payload)
                
                if res.status_code == 200:
                    return True, "Convite enviado com sucesso!"
                
                # Pega a mensagem de erro detalhada da API
                erro_msg = res.json().get("detail", "Erro ao enviar convite.")
                return False, erro_msg

            except Exception as e:
                print(f"[ERRO API] enviar_convite: {e}")
                return False, "Erro de conexão com o servidor."