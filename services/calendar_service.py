from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class CalendarService:
    def __init__(self, email):
        self.email = email
        # Aqui o JIMI carregará o token.json gerado na primeira autenticação
        self.service = build('calendar', 'v3', credentials=self._get_creds())

    def handle(self, action, payload):
        if action == "list_events":
            # Retorna seus próximos compromissos
            events = self.service.events().list(calendarId='primary').execute()
            return events.get('items', [])
        return "Ação de agenda não reconhecida."