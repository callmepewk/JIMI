from flask import Flask, request, jsonify
import threading

class JimiWebServer:
    def __init__(self, port=5000):
        self.app = Flask(__name__)
        self.port = port
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/command", methods=["POST"])
        def command():
            data = request.json
            # Aqui você chama a classe Automation que criamos!
            # from jimi.automation import jimi_core
            # jimi_core.execute(data['command'])
            return jsonify({"status": "executed", "command": data.get("command")})

    def start(self):
        # Roda em thread separada para não bloquear a interface (System Tray)
        server_thread = threading.Thread(
            target=lambda: self.app.run(port=self.port, debug=False, use_reloader=False),
            daemon=True
        )
        server_thread.start()