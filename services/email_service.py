import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("JIMI.EmailService")

class EmailService:
    def __init__(self):
        # Configurações padrão conectadas ao seu ecossistema do Google
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "pedroowkaotaku@gmail.com"
        
        # Senha de aplicativo de 16 dígitos injetada e validada com sucesso
        self.sender_password = "kxwtmbhcdtrarqvz" 

    def handle(self, action: str, payload=None) -> str:
        """
        Ponto de entrada unificado para o ServicesManager do JIMI.
        Sabe lidar com strings diretas ou dicionários estruturados.
        """
        if action == "send":
            # Destinatário padrão configurado no seu painel (seu Outlook)
            to_email = "pedro_hbfreitas@hotmail.com"
            subject = "Relatório de Atividade JIMI"
            body = str(payload)

            # Se o payload for um dicionário estruturado, desempacota os alvos customizados
            if isinstance(payload, dict):
                to_email = payload.get("to", to_email)
                subject = payload.get("subject", subject)
                body = payload.get("body", "")

            return self.send_email(to_email, subject, body)
            
        return f"Ação '{action}' não é suportada pelo módulo de E-mail."

    def send_email(self, to_email: str, subject: str, body_text: str) -> str:
        """Envia um e-mail estruturado via protocolo TLS."""
        if "sua_senha_de_aplicativo" in self.sender_password or self.sender_password == "sua_senha_de_aplicativo_aqui":
            logger.warning("[EMAIL] Envio abortado: Senha de aplicativo padrão ou vazia detectada.")
            return "Configuração pendente: Insira sua Senha de Aplicativo Google no email_service.py."

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Adiciona a assinatura padrão do JIMI no rodapé
        full_body = f"{body_text}\n\nAtenciosamente,\nJIMI - Seu Assistente Pessoal"
        msg.attach(MIMEText(full_body, 'plain', 'utf-8'))

        try:
            logger.info(f"Iniciando conexão TLS com {self.smtp_server}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, to_email, msg.as_string())
            server.quit()
            
            logger.info(f"E-mail enviado com sucesso para {to_email}!")
            return "E-mail enviado com sucesso."
        except Exception as e:
            logger.error(f"Falha ao processar envio de e-mail: {e}")
            return f"Erro ao enviar e-mail: {e}"


# Instanciação global que alimenta o ServicesManager
email_service = EmailService()