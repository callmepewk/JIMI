import threading
import queue
import logging
import requests
import os
import gc
import time
import re

logger = logging.getLogger("JIMI.BuilderEngine")

# ==========================================
# GATEKEEPER: Proteção de dependências móveis
# ==========================================
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("[BuilderEngine] psutil não instalado. Pausa de segurança por RAM desativada.")

class BuilderEngine:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.status = "IDLE"
        
        # Já deixei o IP configurado para o seu setup de rede, mas permitindo override via Variável de Ambiente
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://192.168.1.6:11434/api/generate")
        self.model_name = "phi3" 
        
        # Inicia a thread de processamento em background (Daemon = morre quando o main morre)
        threading.Thread(target=self._process_tasks, daemon=True).start()
        logger.info(f"[BuilderEngine] Motor iniciado ({self.model_name}) apontando para {self.ollama_url}")

    def _check_system_health(self):
        """Verifica se o uso de memória está crítico. Pula a checagem no Android sem psutil."""
        if not PSUTIL_AVAILABLE:
            return True
            
        try:
            mem_usage = psutil.virtual_memory().percent
            if mem_usage > 90:
                logger.warning(f"[BuilderEngine] Memória em {mem_usage}%. Pausa de resfriamento de 30s...")
                time.sleep(30)
                return False
            return True
        except Exception as e:
            logger.error(f"[BuilderEngine] Erro na leitura térmica/memória: {e}")
            return True 

    def add_task(self, task_name, meta):
        self.task_queue.put({"name": task_name, "meta": meta})
        logger.info(f"[BuilderEngine] Nova tarefa enfileirada: {task_name}")
        return f"Tarefa '{task_name}' na fila."

    def _limpar_codigo_llm(self, texto_bruto: str) -> str:
        """
        Extrator Cirúrgico: Remove conversinha do LLM e formatações markdown.
        Garante que o arquivo salvo seja um código Python válido.
        """
        texto = texto_bruto.strip()
        
        # Expressão regular para remover ```python e ``` 
        texto = re.sub(r"^```[a-zA-Z]*\n", "", texto)
        texto = re.sub(r"\n```$", "", texto)
        
        # Fallback caso a IA coloque texto ANTES do bloco de código
        if "```" in texto:
            partes = texto.split("```")
            if len(partes) >= 3:
                # Pega o conteúdo do primeiro bloco de código que encontrar
                texto = partes[1]
                if texto.startswith("python\n") or texto.startswith("python3\n"):
                    texto = texto.split("\n", 1)[1]
                    
        return texto.strip() + "\n" # Garante uma linha vazia no final (padrão PEP8)

    def _process_tasks(self):
        """Loop principal do Worker."""
        while True:
            task = self.task_queue.get()
            
            # Checagem de segurança (Backpressure)
            if not self._check_system_health():
                self.task_queue.put(task) 
                time.sleep(5) # Evita loop infinito fritando a CPU se a RAM não baixar
                continue

            try:
                self.status = f"WORKING: {task['name']}"
                file_path = task['meta'].get('path')
                
                if not file_path or not os.path.exists(file_path):
                    logger.error(f"[BuilderEngine] Arquivo não encontrado: {file_path}")
                    continue

                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read(50000) # Limite de 50KB por segurança
                
                # Engenharia de Prompt Avançada
                prompt = (
                    "Você é um Arquiteto de Software Sênior especializado em Python limpo e performático.\n"
                    "Sua tarefa é refatorar o código abaixo para máxima eficiência, seguindo a PEP8.\n\n"
                    "REGRAS ABSOLUTAS:\n"
                    "1. Retorne EXCLUSIVAMENTE o código fonte funcional.\n"
                    "2. NÃO diga 'Aqui está o código' ou qualquer outra explicação.\n"
                    "3. O código deve estar pronto para execução imediata.\n\n"
                    f"CÓDIGO ORIGINAL:\n{code_content}"
                )
                
                logger.info(f"[BuilderEngine] Solicitando refatoração para: {file_path}")
                resposta_bruta = self._chamar_ollama(prompt)
                
                if "# Erro" in resposta_bruta:
                    logger.error(f"[BuilderEngine] Falha na IA. Abortando tarefa {task['name']}")
                    continue

                # Passa pelo sanitizador para garantir que não vai quebrar o script
                codigo_limpo = self._limpar_codigo_llm(resposta_bruta)
                
                # Salva o backup (.new) para não destruir o código original acidentalmente
                new_path = f"{file_path}.new"
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(codigo_limpo)
                
                logger.info(f"[BuilderEngine] Sucesso! Novo código salvo em: {new_path}")
                
            except Exception as e:
                logger.error(f"[BuilderEngine] Erro crítico na tarefa {task['name']}: {e}")
            finally:
                self.status = "IDLE"
                self.task_queue.task_done()
                gc.collect() 

    def _chamar_ollama(self, prompt, retries=2):
        """Camada de comunicação resiliente com o modelo."""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,     # Aumentado para 4K para não cortar códigos grandes
                "temperature": 0.1   # Temperatura baixa = IA foca em código sem ser criativa/tagarela
            } 
        }
        
        for tentativa in range(retries):
            try:
                # Timeout flexível (LLMs locais demoram para processar código grande)
                response = requests.post(self.ollama_url, json=payload, timeout=240)
                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    logger.warning(f"[BuilderEngine] Ollama retornou status {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"[BuilderEngine] Tentativa {tentativa + 1} falhou. Erro de rede: {e}")
                time.sleep(2) # Espera antes de tentar de novo
                
        return "# Erro Ollama: Falha após múltiplas tentativas."

# Instância global
builder_engine = BuilderEngine()