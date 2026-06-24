import os
import re
import time
import threading
import subprocess
import logging
from flask import Flask, request, jsonify
from core.security import security_manager

# Configuração rigorosa de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] (%(name)s) - %(message)s')
logger = logging.getLogger("JIMI.NetworkBridge")

app = Flask(__name__)

# Configurações de Segurança e Credenciais
SECRET_TOKEN = "JIMI_PEDRO_2026_SECRET"

# Gerenciamento dinâmico de caminhos absolutos (Root do projeto JIMI)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.log")
ARQUIVO_URL_TUNNEL = os.path.join(BASE_DIR, "tunnel_url.txt")

class NetworkBridgeService:
    def __init__(self):
        self.server_thread = None
        self.tunnel_watcher_thread = None
        self.running = False
        self._ultima_url_detectada = ""

    def start_all(self):
        """Inicializa todos os motores da ponte de rede de forma assíncrona."""
        if self.running:
            logger.warning("Os serviços de rede já estão em execução.")
            return "Serviços já operantes."

        self.running = True
        
        # 1. Inicializa o Servidor de API Flask
        self.server_thread = threading.Thread(target=self._run_flask, daemon=True, name="JIMI-FlaskServer")
        self.server_thread.start()
        
        # 2. Inicializa o Observador do Túnel Cloudflare (Auto-update no GitHub)
        self.tunnel_watcher_thread = threading.Thread(target=self._watch_cloudflare_tunnel, daemon=True, name="JIMI-TunnelWatcher")
        self.tunnel_watcher_thread.start()

        logger.info("Módulos de ponte de rede e monitoramento de infraestrutura iniciados.")
        return "Servidor API e Monitor do Cloudflare ativos."

    def _run_flask(self):
        """Executa a engine interna do Flask suprimindo logs excessivos de debug."""
        try:
            cli = logging.getLogger('werkzeug')
            cli.setLevel(logging.ERROR)  # Evita poluir o terminal com requisições HTTP normais
            logger.info("API Gateway rodando localmente na porta 5000 (Aguardando túnel...)")
            app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
        except Exception as e:
            logger.critical(f"Falha fatal no servidor HTTP Flask: {e}")

    def _git_push_url(self, nova_url: str):
        """Executa operações do Git de forma isolada e segura para não travar a aplicação."""
        try:
            # Salva localmente primeiro
            with open(ARQUIVO_URL_TUNNEL, "w", encoding="utf-8") as f:
                f.write(nova_url)

            logger.info("Sincronizando nova URL do túnel com o repositório Git...")
            
            # Executa os comandos utilizando caminhos absolutos de execução do Git
            subprocess.run(["git", "add", ARQUIVO_URL_TUNNEL], cwd=BASE_DIR, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "infra: auto update tunnel url [skip ci]"], cwd=BASE_DIR, check=True, capture_output=True)
            subprocess.run(["git", "push"], cwd=BASE_DIR, check=True, capture_output=True)
            
            logger.info("Repositório atualizado com sucesso. O iOS já pode consumir a nova rota.")
            self._ultima_url_detectada = nova_url
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao interagir com o Git (Push falhou): {e.stderr.decode().strip()}")
        except Exception as e:
            logger.error(f"Erro inesperado no pipeline de sincronização de infraestrutura: {e}")

    def _watch_cloudflare_tunnel(self):
        """Monitora continuamente o arquivo cloudflared.log em busca de novas conexões."""
        logger.info("Observador de túnel ativado. Aguardando a inicialização do cloudflared...")
        
        # Aguarda a criação inicial do arquivo de logs pelo subsistema de boot
        tentativas = 0
        while not os.path.exists(LOG_CLOUDFLARED) and tentativas < 30:
            time.sleep(1)
            tentativas += 1

        if not os.path.exists(LOG_CLOUDFLARED):
            logger.error("Arquivo cloudflared.log não foi detectado no diretório raiz após 30s. Monitor abortado.")
            return

        # Loop eterno de monitoramento (Caso o túnel caia e mude de URL nas próximas 24h)
        while self.running:
            try:
                if os.path.exists(LOG_CLOUDFLARED):
                    with open(LOG_CLOUDFLARED, "r", encoding="utf-8", errors="ignore") as f:
                        conteudo = f.read()

                    # Expressão regular industrial para capturar o padrão exato da URL temporária do Cloudflare
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", conteudo)
                    
                    if match:
                        url_encontrada = match.group(0)
                        
                        # Só envia para o Git se o link mudou (evita commits infinitos duplicados)
                        if url_encontrada != self._ultima_url_detectada:
                            logger.info(f"Nova rota dinâmica identificada: {url_encontrada}")
                            self._git_push_url(url_encontrada)
            except Exception as e:
                logger.error(f"Erro no loop do observador de infraestrutura: {e}")
            
            # Aguarda 10 segundos entre verificações de mudança de link
            time.sleep(10)

    def handle(self, action: str, payload=None):
        """Ponto de entrada unificado para controle do ciclo de vida via Manager."""
        if action == "start":
            return self.start_all()
        return f"Ação '{action}' não suportada."


# --- MAPEAMENTO DE ROTAS DA API HTTP ---

@app.route('/status', methods=['GET'])
def health_check():
    """Endpoint leve para checagem rápida de integridade do sistema pelo iOS."""
    return jsonify({
        "status": "online",
        "modulo": "JIMI.NetworkBridge",
        "tunnel_ativo": network_bridge_service._ultima_url_detectada
    }), 200


@app.route('/command', methods=['POST'])
def receive_command():
    """Processa comandos externos com validação de assinatura digital via Header."""
    # 1. Validação Crítica do Token
    token = request.headers.get('X-JIMI-TOKEN')
    if token != SECRET_TOKEN:
        logger.warning(f"Tentativa ilegal de acesso bloqueada! IP Origem: {request.remote_addr}")
        return jsonify({"status": "erro", "mensagem": "Token de autenticação inválido"}), 403

    # 2. Extração e sanitização de Payload
    data = request.json
    if not data:
        return jsonify({"status": "erro", "mensagem": "Payload JSON ausente ou corrompido"}), 400

    logger.info(f"Comando recebido de canal seguro: {data}")
    
    try:
        # Injeção dinâmica do executor principal
        from core.executor import execute
        result = execute(data)
        return jsonify({"status": "sucesso", "resultado": result}), 200
    except Exception as e:
        logger.error(f"Falha na execução do pipeline de comandos: {e}")
        return jsonify({"status": "erro", "mensagem": f"Internal Server Error: {e}"}), 500


# Instanciação estática para o ecossistema
network_bridge_service = NetworkBridgeService()

if __name__ == "__main__":
    # Teste de execução isolada do script
    network_bridge_service.start_all()
    # Mantém a thread principal viva para testes locais de prateleira
    while True:
        time.sleep(1)