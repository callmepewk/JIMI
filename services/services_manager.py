import logging
from .calendar_service import CalendarService
from .whatsapp_service import WhatsAppService
from .email_service import EmailService

class ServicesManager:
    def __init__(self):
        self.logger = logging.getLogger("JIMI.ServicesManager")
        # Configurações de Identidade
        self.config = {
            "whatsapp": {"phone": "+5554991554136"},
            "google": {"email": "pedroowkaotaku@gmail.com"},
            "outlook": {"email": "pedro_hbfreitas@hotmail.com"}
        }
        
        # Inicialização dos serviços
        self.calendar = CalendarService(self.config["google"]["email"])
        self.whatsapp = WhatsAppService(self.config["whatsapp"]["phone"])
        self.email = EmailService(self.config["google"]["email"], self.config["outlook"]["email"])

    def execute_task(self, service_name, action, payload):
        """
        Hub de roteamento. 
        Ex: services_manager.execute_task('whatsapp', 'send', 'Olá!')
        """
        try:
            service = getattr(self, service_name, None)
            if not service:
                return f"Serviço {service_name} não encontrado."
            
            # Executa a ação específica no módulo de serviço
            return service.handle(action, payload)
        except Exception as e:
            self.logger.error(f"Erro no serviço {service_name}: {e}")
            return f"Erro na conexão com {service_name}."

# Instância global
services_manager = ServicesManager()