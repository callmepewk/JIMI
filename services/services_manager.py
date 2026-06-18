import logging
from services.calendar_service import calendar_service
from services.whatsapp_service import whatsapp_service
from services.email_service import email_service
from services.camera_service import camera_service
from services.network_service import network_service
from services.maps_service import maps_service
from services.system_service import system_service
from services.voice_service import voice_service
from services.network_bridge_service import network_bridge_service

logger = logging.getLogger("JIMI.ServicesManager")

class ServicesManager:
    def __init__(self):
        # Configurações globais centralizadas
        self.config = {
            "whatsapp": {"phone": "+5554991554136"},
            "google": {"email": "pedroowkaotaku@gmail.com"},
            "outlook": {"email": "pedro_hbfreitas@hotmail.com"}
        }
        
        # Mapeamento do ecossistema de serviços
        self.services = {
            "calendar": calendar_service,
            "whatsapp": whatsapp_service,
            "email": email_service,
            "camera": camera_service,
            "network": network_service,
            "maps": maps_service,
            "system": system_service,
            "voice": voice_service,
            "bridge": network_bridge_service
        }

    def execute_task(self, service_name: str, action: str, payload=None):
        """
        Hub Central de Roteamento de Comandos.
        Delegado exclusivamente para a interface .handle() de cada serviço.
        """
        logger.info(f"[SERVICES] Roteando -> Serviço: {service_name} | Ação: {action}")
        
        service = self.services.get(service_name)
        
        if not service:
            error_msg = f"Serviço '{service_name}' está offline ou não implementado."
            logger.warning(error_msg)
            return error_msg
        
        try:
            # Roteamento puramente delegativo: 
            # O Manager não precisa saber o que o serviço faz, apenas que ele sabe lidar com a tarefa.
            return service.handle(action, payload)
            
        except Exception as e:
            logger.error(f"[SERVICES ERROR] Falha crítica ao delegar {action} para {service_name}: {e}")
            return {"error": str(e)}

# Instância unificada global
services_manager = ServicesManager()