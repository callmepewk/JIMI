import threading
from flask import Flask, request, jsonify
import logging

logger = logging.getLogger("JIMI.ServerService")
app = Flask(__name__)

class ServerService:
    def __init__(self):
        self.server_thread = None

    def start_server(self):
        """Inicia o servidor de escuta remota em uma thread."""
        def run():
            app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        logger.info("Servidor de comandos remotos (Bridge) iniciado na porta 5000.")

    def handle(self, action: str, payload=None):
        if action == "start":
            self.start_server()
            return "Servidor remoto iniciado."
        return "Ação não suportada."

# Endpoint de recepção de comandos do celular
@app.route('/command', methods=['POST'])
def receive_command():
    data = request.json
    logger.info(f"Comando remoto recebido: {data}")
    # Aqui você integraria com o executor central posteriormente
    return jsonify({"status": "recebido", "data": data})

server_service = ServerService()