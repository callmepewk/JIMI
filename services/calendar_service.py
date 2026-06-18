import os
import logging
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class CalendarService:
    # Escopo necessário para ler e gerenciar compromissos da agenda
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, email=None):
        self.logger = logging.getLogger("JIMI.Calendar")
        self.email = email
        self.service = None
        
        try:
            # Inicializa as credenciais e constrói o cliente da API do Google
            creds = self._get_creds()
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Serviço de Google Calendar inicializado com sucesso.")
        except Exception as e:
            self.logger.error(f"Falha crítica na inicialização do Google Calendar: {e}")

    def _get_creds(self):
        """Gerencia a autenticação do Google Cloud e geração/atualização de tokens"""
        creds = None
        # Caminhos absolutos/relativos baseados na pasta do serviço
        token_path = os.path.join('services', 'token.json')
        credentials_path = os.path.join('services', 'credentials.json')

        # 1. Tenta carregar um token de acesso já existente e salvo
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
                self.logger.info("Token existente carregado com sucesso.")
            except Exception as e:
                self.logger.error(f"Erro ao ler token.json: {e}. Criando um novo fluxo.")

        # 2. Se o token não existir ou for inválido, fazemos a validação ou atualização
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    self.logger.info("Token expirado. Tentando atualizar com o Refresh Token...")
                    creds.refresh(Request())
                except Exception:
                    self.logger.warning("Falha ao atualizar token. Forçando novo login.")
                    creds = None
            
            # Se ainda assim não tivermos credenciais válidas, abre o navegador para login
            if not creds:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(
                        f"Arquivo '{credentials_path}' não encontrado. "
                        "Certifique-se de que o arquivo baixado do Google Cloud está nomeado exatamente como 'credentials.json'."
                    )
                
                self.logger.info("Iniciando fluxo de autenticação via navegador...")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 3. Salva as novas credenciais válidas no token.json para o próximo boot
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
                self.logger.info("Novo token.json gerado e salvo com sucesso.")

        return creds

    def handle(self, action: str, payload=None):
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        Roteia os comandos dinamicamente.
        """
        if not self.service:
            return "O serviço de agenda está indisponível no momento."

        if action == "list":
            # Converte o payload para int se for enviado um limite customizado
            max_results = int(payload) if payload and str(payload).isdigit() else 5
            return self.list_events(max_results=max_results)
            
        return f"Ação '{action}' não é suportada pelo módulo de Calendário."

    def list_events(self, max_results=5):
        """Roda a consulta na API do Google para trazer os próximos compromissos"""
        try:
            # Correção para o Python 3.14 (utcnow() descontinuado)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            
            events_result = self.service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])

            if not events:
                return "Não encontrei nenhum compromisso agendado nos seus próximos registros, Sr. Pedro."

            reply = "Aqui estão seus próximos compromissos, Sr. Pedro:\n\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Formatação legível de data e hora
                if 'T' in start:
                    date_part, time_part = start.split('T')
                    time_str = time_part[:5]
                else:
                    date_part = start
                    time_str = "Dia inteiro"
                
                # Inverte a data para padrão BR (AAAA-MM-DD -> DD/MM/AAAA)
                date_br = "/".join(date_part.split("-")[::-1])
                reply += f"📅 *{event['summary']}*\n⏱️ {date_br} às {time_str}\n\n"
            
            return reply.strip()

        except Exception as e:
            self.logger.error(f"Erro ao listar eventos da agenda: {e}")
            return f"Desculpe, falhei ao acessar sua agenda de compromissos: {e}"


# --- A CORREÇÃO CRÍTICA: Instanciação global que resolve o erro do ServicesManager ---
calendar_service = CalendarService()