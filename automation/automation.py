import os
import subprocess
import webbrowser
import logging
import threading
import queue
import requests
import pyautogui

# Integração nativa com o Hub de Serviços do JIMI
from services.services_manager import services_manager

logger = logging.getLogger("JIMI.Automation")


class JimiAutomation:
    def __init__(self):
        self.pyautogui = pyautogui
        self.pyautogui.PAUSE = 0.15  # Reduzido levemente para maior agilidade nas ações
        self.pyautogui.FAILSAFE = True  # Arrastar o mouse para o canto superior esquerdo para travar o script se der pane
        
        self.context = {"waiting_spotify": False}
        
        # --- Sistema de Filas Assíncronas ---
        self.task_queue = queue.Queue()
        self._stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._process_queue, name="JIMI_WorkerThread", daemon=True)
        self.worker_thread.start()
        
        logger.info("Sistema de Automação Assíncrona do JIMI ativo e operando em background.")

    def submit_command(self, text: str, callback=None):
        """
        Injeta uma requisição de automação na fila de execução assíncrona.
        Opcionalmente executa uma função de callback enviando a resposta obtida.
        """
        if text and text.strip():
            logger.info(f"[FILA] Novo comando enviado para a esteira: '{text}'")
            self.task_queue.put((text, callback))

    def _process_queue(self):
        """Consumidor contínuo da fila. Garante a execução linear e ordenada dos comandos."""
        while not self._stop_event.is_set():
            try:
                # Timeout curto para permitir que a thread interrompa o loop rapidamente no encerramento
                task = self.task_queue.get(timeout=0.5)
                text, callback = task
                
                # Execução da inteligência de roteamento
                result_message = self.process_command(text)
                
                # Devolve a resposta para quem solicitou (ex: interface, logs, etc.)
                if callback:
                    try:
                        callback(result_message)
                    except Exception as cb_err:
                        logger.error(f"[CALLBACK ERROR] Falha ao responder interface: {cb_err}")
                
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.critical(f"[WORKER CRITICAL] Falha na esteira de automação: {e}")

    def safe_execute(self, func, *args, **kwargs):
        """Wrapper de contenção. Impede que erros de IO de hardware derrubem o processo central."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[EXECUTION ERROR] Falha ao rodar {func.__name__ if hasattr(func, '__name__') else 'lambda'}: {e}")
            return None

    def open_app(self, app_name: str):
        """Lança aplicações locais aplicando fallbacks inteligentes de diretórios conhecidos."""
        # Mapeamento de rotas estáticas absolutas para contornar falhas de PATH de ambiente
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
        fallbacks = {
            "spotify": [
                "spotify",
                f"{user_profile}\\AppData\\Roaming\\Spotify\\Spotify.exe",
                f"{os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')}\\Spotify\\Spotify.exe"
            ],
            "code": [
                "code",
                f"{user_profile}\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"
            ]
        }

        paths_to_try = fallbacks.get(app_name, [app_name])
        
        for path in paths_to_try:
            try:
                # shell=True permite achar aliases do sistema, mas passamos caminhos isolados para proteção
                subprocess.Popen(path, shell=True if path == app_name else False)
                logger.info(f"[LAUNCH] Aplicativo iniciado com sucesso: {path}")
                return True
            except Exception:
                continue
                
        logger.error(f"[LAUNCH FAILED] Não foi possível encontrar rotas para o aplicativo: {app_name}")
        return False

    def perform_system_action(self, action: str) -> str:
        """Executa chamadas diretas de controle de hardware e energia do Sistema Operacional."""
        actions = {
            "shutdown": lambda: os.system("shutdown /s /t 5"),  # 5 segundos de tolerância para segurança
            "restart": lambda: os.system("shutdown /r /t 5"),
            "mute": lambda: self.pyautogui.press("volumemute")
        }
        
        if action in actions:
            execution = self.safe_execute(actions[action])
            if execution is not None:
                return f"Protocolo de sistema '{action}' executado com sucesso, Sr. Pedro."
            return "Houve um erro físico ao tentar aplicar o comando de sistema."
        return "Comando de infraestrutura não reconhecido."

    def smart_search(self, query: str) -> str:
        """Busca instantânea na Web usando DuckDuckGo API (Modo de Baixa Latência)."""
        if not query.strip():
            return "O que o senhor deseja pesquisar na rede, Sr. Pedro?"
            
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
            response = requests.get(url, timeout=4)
            response.raise_for_status()
            data = response.json()
            
            abstract = data.get("AbstractText")
            if abstract:
                return abstract
                
            # Fallback 1: Busca por tópicos relacionados caso o abstract principal venha vazio
            related = data.get("RelatedTopics")
            if related and isinstance(related, list) and "Text" in related[0]:
                return related[0]["Text"]
                
            return f"Não encontrei um resumo imediato para '{query}', Sr. Pedro. Deseja que eu abra o navegador?"
        except requests.exceptions.RequestException as e:
            logger.warning(f"[NET SEARCH ERROR] DuckDuckGo inacessível: {e}")
            return "Minha conexão com os servidores externos falhou. Verifique nossos adaptadores de rede."

    def consult_brain(self, text: str) -> str:
        """Encaminha consultas complexas ou conversas livres para o Cérebro de IA do JIMI."""
        logger.info(f"[COGNITIVE ROUTE] Encaminhando intenção para a LLM: '{text}'")
        try:
            from core.brain import jimi_brain
            
            # Executa garantindo que o cérebro saiba que a chamada veio de dentro da automação
            # para evitar que ele tente re-disparar loops de comandos idênticos.
            if hasattr(jimi_brain, 'think'):
                return jimi_brain.think(text)
            return "Módulo central de inteligência carregado, mas as funções de pensamento estão desconectadas."
        except ImportError:
            logger.error("[MODULE ERROR] Impossível importar 'core.brain'. Verifique a árvore de arquivos.")
            return "Estou operando apenas em modo de hardware, Sr. Pedro. Meu córtex de IA está inacessível."
        except Exception as e:
            logger.error(f"[COGNITIVE ERROR] Erro na resposta do cérebro: {e}")
            return "Houve uma anomalia de processamento nos meus neurônios artificiais."

    def process_command(self, text: str) -> str:
        """Roteador Central de Intenções. Filtra e decide o destino de cada ordem recebida."""
        text = text.lower().strip()
        
        if not text:
            return "Aguardando suas ordens, Sr. Pedro."

        # 1. Roteamento para Hub de Integrações Externas (Calendar / WhatsApp)
        if "agenda" in text or "compromissos" in text:
            return services_manager.execute_task('calendar', 'list_events', {})
        
        if "whatsapp" in text and ("enviar" in text or "manda" in text):
            return services_manager.execute_task('whatsapp', 'send', text)
            
        # 2. Comandos Diretos de Controle do Sistema Operacional
        if text.startswith("abrir "):
            app_target = text.replace("abrir ", "").strip()
            return self._handle_open_intent(app_target)
            
        if text.startswith("pesquisar "):
            query_target = text.replace("pesquisar ", "").strip()
            return self.smart_search(query_target)
            
        if "desligar o sistema" in text or "desligar computador" in text:
            return self.perform_system_action("shutdown")
            
        if "mutar" in text or "silenciar" in text or "remover som" in text:
            return self.perform_system_action("mute")
            
        # 3. Fallback Cognitivo: Se não é um gatilho de hardware idêntico, a LLM assume a conversa
        return self.consult_brain(text)

    def _handle_open_intent(self, app_name: str) -> str:
        """Valida e processa o alvo a ser aberto (Web ou Software Local)."""
        mapping = {
            "spotify": "spotify",
            "vscode": "code",
            "vs code": "code",
            "visual studio": "code",
            "navegador": "https://google.com",
            "google": "https://google.com",
            "whatsapp web": "https://web.whatsapp.com"
        }
        
        # Procura correspondência de chaves dentro da string do app_name
        for key, target in mapping.items():
            if key in app_name:
                if target.startswith("http"):
                    webbrowser.open(target)
                    return f"Direcionando o navegador para o {key}, Sr. Pedro."
                else:
                    success = self.open_app(target)
                    if success:
                        return f"Iniciando o {key} imediatamente, Sr. Pedro."
                    return f"Tentei abrir o {key}, mas o binário do sistema não respondeu."
                    
        # Caso não esteja no dicionário, tenta lançar o nome cru como comando de sistema de última hora
        if self.open_app(app_name):
            return f"Executando comando para abrir '{app_name}'."
            
        return f"Não encontrei um atalho registrado para '{app_name}' em meus bancos de dados."

    def shutdown_jimi(self):
        """Encerra a esteira de tarefas de forma limpa, aguardando finalizações críticas."""
        logger.info("Encerrando barramento de automação...")
        self._stop_event.set()
        try:
            self.worker_thread.join(timeout=2.0)
            logger.info("Worker Thread desativada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao forçar parada na thread de automação: {e}")


# Instância global e segura para importação nos demais módulos
jimi_core = JimiAutomation()