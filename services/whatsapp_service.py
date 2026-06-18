import webbrowser
import time
import urllib.parse
import pyautogui
import logging

logger = logging.getLogger("JIMI.WhatsAppService")

class WhatsAppService:
    def handle(self, action: str, payload=None):
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        Orquestra o disparo de mensagens para o WhatsApp Web.
        """
        if action == "send_message":
            if isinstance(payload, dict):
                phone = payload.get("phone")
                message = payload.get("message")
                if phone and message:
                    return self.send_direct_message(str(phone), str(message))
            return "Erro: Payload inválido. Forneça um dicionário com 'phone' e 'message'."
            
        return f"Ação '{action}' não é suportada pelo módulo de WhatsApp."

    def send_direct_message(self, phone_number: str, message_text: str) -> str:
        """
        Abre o WhatsApp Web direto na conversa do número indicado,
        insere o texto digitado e adiciona a assinatura em negrito.
        """
        logger.info(f"Preparando envio de mensagem para o canal: {phone_number}")
        
        # Concatena a assinatura oficial do assistente
        final_message = f"{message_text}\n\n*Jimi*"
        
        # Codifica o texto para formato de URL válida
        encoded_text = urllib.parse.quote(final_message)
        wp_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_text}"
        
        # Dispara a abertura no navegador padrão
        webbrowser.open(wp_url)
        
        logger.info("Aguardando carregamento da interface gráfica do WhatsApp Web (12s)...")
        time.sleep(12) 
        
        # Pressiona Enter simulando o teclado físico para enviar
        pyautogui.press("enter")
        logger.info("Comando de disparo enviado para o chat.")
        return f"Mensagem enviada com sucesso para {phone_number}."

    def format_contact_message(self, contact_name: str, message_text: str):
        """Método de apoio para quando o JIMI usa busca semântica por nome."""
        pass


# Instanciação global necessária para o circuito do ServicesManager
whatsapp_service = WhatsAppService()