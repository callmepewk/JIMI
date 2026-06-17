import pywhatkit

class WhatsAppService:
    def __init__(self, phone):
        self.phone = phone # +5554991554136

    def handle(self, action, payload):
        if action == "send":
            # Envia mensagem diretamente do seu PC
            pywhatkit.sendwhatmsg_instantly(self.phone, payload)
            return "Mensagem enviada com sucesso."
        return "Ação de WhatsApp não reconhecida."