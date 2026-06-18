import logging
import threading
from flask import Flask, request, jsonify, render_template_string

# Tenta importar Flask-CORS caso você queira conectar painéis Web ao JIMI futuramente
try:
    from flask_cors import CORS
    cors_available = True
except ImportError:
    cors_available = False

# Amarração direta com o núcleo cognitivo unificado do JIMI
from core.brain import jimi_brain as brain

logger = logging.getLogger("JIMI.WebServer")

# --- INTERFACE WEB (HTML + CSS + JS) ---
# Totalmente responsiva para funcionar perfeitamente no celular
HTML_PORTAL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>JIMI OS - Portal de Comando</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #ffffff; text-align: center; padding: 20px; margin: 0; }
        h1 { color: #00ffcc; margin-bottom: 5px; }
        p.subtitle { color: #888; font-size: 0.9em; margin-top: 0; margin-bottom: 20px; }
        #chat-box { background: #1e1e1e; border-radius: 10px; padding: 15px; min-height: 200px; margin-bottom: 20px; text-align: left; overflow-y: auto; max-height: 50vh; border: 1px solid #333; }
        .msg { margin-bottom: 10px; line-height: 1.4; }
        .msg-user { color: #00ffcc; font-weight: bold; }
        .msg-jimi { color: #ffffff; }
        .controls { display: flex; flex-direction: column; gap: 10px; }
        input[type="text"] { padding: 12px; border-radius: 8px; border: none; background: #333; color: white; font-size: 16px; outline: none; }
        .btn-row { display: flex; gap: 10px; justify-content: center; }
        button { padding: 12px 20px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; transition: 0.2s; }
        button.send { background: #00ffcc; color: #000; flex-grow: 1; }
        button.mic { background: #ff4444; color: #fff; }
        button.upload { background: #444; color: #fff; }
        input[type="file"] { display: none; }
        #loading { display: none; color: #00ffcc; font-size: 0.9em; margin-top: 10px; }
    </style>
</head>
<body>

    <h1>JIMI OS</h1>
    <p class="subtitle">Acesso Remoto Seguro</p>

    <div id="chat-box">
        <div class="msg"><span class="msg-jimi">JIMI: Aguardando comandos, Sr. Pedro.</span></div>
    </div>
    
    <div id="loading">Processando no núcleo cognitivo...</div>

    <div class="controls">
        <input type="text" id="cmd" placeholder="Digite seu comando ou fale..." onkeypress="handleEnter(event)">
        <input type="file" id="fileInput" accept="image/*,.pdf,.txt">
        
        <div class="btn-row">
            <button class="mic" onclick="startDictation()">🎤 Voz</button>
            <button class="upload" onclick="document.getElementById('fileInput').click()">📎 Arquivo</button>
            <button class="send" onclick="send()">Enviar</button>
        </div>
    </div>

    <script>
        let base64File = null;

        // Converter arquivo para Base64 quando selecionado
        document.getElementById('fileInput').addEventListener('change', function(e) {
            let file = e.target.files[0];
            if (!file) return;
            let reader = new FileReader();
            reader.onloadend = function() {
                base64File = reader.result;
                addMessage("Sistema", "Arquivo carregado: " + file.name, "#888");
            }
            reader.readAsDataURL(file);
        });

        // Captura de Voz via Web Speech API
        function startDictation() {
            if (window.hasOwnProperty('webkitSpeechRecognition') || window.hasOwnProperty('SpeechRecognition')) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const recognition = new SpeechRecognition();
                recognition.lang = 'pt-BR';
                recognition.continuous = false;
                recognition.interimResults = false;
                
                recognition.onstart = function() { document.getElementById('cmd').placeholder = "Ouvindo..."; };
                recognition.onresult = function(e) {
                    document.getElementById('cmd').value = e.results[0][0].transcript;
                    document.getElementById('cmd').placeholder = "Digite seu comando ou fale...";
                };
                recognition.onerror = function(e) { document.getElementById('cmd').placeholder = "Erro no microfone."; };
                recognition.start();
            } else {
                alert("Seu navegador não suporta reconhecimento de voz nativo.");
            }
        }

        // Enviar com Enter
        function handleEnter(e) { if (e.key === 'Enter') send(); }

        function addMessage(sender, text, color) {
            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += `<div class="msg"><span style="color:${color}; font-weight:bold;">${sender}:</span> <span class="msg-jimi">${text}</span></div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        // Envio do payload para o PC
        function send() {
            let cmdInput = document.getElementById('cmd');
            let text = cmdInput.value.trim();
            if (!text && !base64File) return;

            addMessage("Pedro", text ? text : "[Arquivo Enviado]", "#00ffcc");
            cmdInput.value = '';
            document.getElementById('loading').style.display = 'block';

            let payload = { command: text, file: base64File };

            fetch('/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                let resposta = data.jimi_response || data.error || "Sem resposta.";
                addMessage("JIMI", resposta, "#ffffff");
                
                // JIMI FALA A RESPOSTA (TTS)
                let fala = new SpeechSynthesisUtterance(resposta);
                fala.lang = 'pt-BR';
                window.speechSynthesis.speak(fala);
                
                // Limpa o anexo após enviar
                base64File = null; 
            })
            .catch(err => {
                document.getElementById('loading').style.display = 'none';
                addMessage("Erro", "Falha de conexão com o servidor local.", "#ff4444");
            });
        }
    </script>
</body>
</html>
"""

class JimiWebServer:
    def __init__(self, port=5000, host="0.0.0.0"):
        self.app = Flask(__name__)
        self.port = port
        self.host = host
        
        if cors_available:
            CORS(self.app)
            
        self._setup_routes()

    def _setup_routes(self):
        
        # 1. ROTA DA INTERFACE WEB (Para acessar pelo celular)
        @self.app.route("/", methods=["GET"])
        def home():
            return render_template_string(HTML_PORTAL)

        # 2. ROTA DE STATUS
        @self.app.route("/status", methods=["GET"])
        def status():
            return jsonify({"status": "online", "system": "JIMI OS"}), 200

        # 3. ROTA DE COMANDO (Recebe do Frontend)
        @self.app.route("/command", methods=["POST"])
        def command():
            data = request.json
            
            if not data:
                return jsonify({"status": "error", "message": "Payload inválido."}), 400
                
            command_text = data.get("command", "").strip()
            file_base64 = data.get("file", None) # Captura a imagem/arquivo se houver
            
            # Se tivermos um arquivo, podemos no futuro avisar o cérebro
            # Exemplo: response_text = brain.think(command_text, image=file_base64)
            
            try:
                logger.info(f"[API HTTP] Requisição recebida: '{command_text}' (Anexo: {'Sim' if file_base64 else 'Não'})")
                
                # Chamada ao cérebro (por enquanto passando apenas o texto)
                response_text = brain.think(command_text)
                
                return jsonify({
                    "status": "success",
                    "jimi_response": response_text
                }), 200
                
            except Exception as e:
                logger.error(f"[API ERROR] Falha ao processar comando HTTP: {e}")
                return jsonify({"status": "failed", "error": str(e)}), 500

    def start(self):
        server_thread = threading.Thread(
            target=lambda: self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False),
            daemon=True
        )
        server_thread.start()
        print(f"[✓] Portal JIMI Web ativo. Acesse via Cloudflare Tunnel ou http://localhost:{self.port}")

web_server = JimiWebServer()