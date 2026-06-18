import threading
from flask import Flask, request, jsonify
import logging
from core.security import security_manager

logger = logging.getLogger("JIMI.NetworkBridge")
app = Flask(__name__)

# CHAVE SECRETA: Mantenha isso privado! 
# No futuro, pode vir de um arquivo .env
SECRET_TOKEN = "JIMI_PEDRO_2026_SECRET" 

class NetworkBridgeService:
    def __init__(self):
        self.server_thread = None

    def start_server(self):
        def run():
            cli = logging.getLogger('werkzeug')
            cli.setLevel(logging.ERROR)
            app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        logger.info("Ponte de Rede (Bridge) ativa com Autenticação via Token.")

    def handle(self, action: str, payload=None):
        if action == "start":
            self.start_server()
            return "Servidor de ponte remota iniciado."
        return f"Ação '{action}' não suportada."

@app.route('/command', methods=['POST'])
def receive_command():
    # 1. Validação do Token
    token = request.headers.get('X-JIMI-TOKEN')
    if token != SECRET_TOKEN:
        logger.warning("Tentativa de acesso não autorizado detectada!")
        return jsonify({"status": "erro", "mensagem": "Token inválido"}), 403

    # 2. Processamento do Comando
    data = request.json
    logger.info(f"Comando autenticado via Bridge: {data}")
    
    # Integração com o Executor
    from core.executor import execute
    result = execute(data)
    
    return jsonify({"status": "sucesso", "resultado": result})

network_bridge_service = NetworkBridgeService()