import threading
import queue
import logging
import requests
import os
import gc
import time
import psutil  

logger = logging.getLogger("JIMI.BuilderEngine")

class BuilderEngine:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.status = "IDLE"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "phi3" 
        
        # Inicia a thread de processamento em background
        threading.Thread(target=self._process_tasks, daemon=True).start()
        logger.info(f"[BuilderEngine] Motor iniciado com modelo {self.model_name}.")

    def _check_system_health(self):
        """Verifica se o uso de memória está crítico (acima de 90%) antes de processar."""
        try:
            mem_usage = psutil.virtual_memory().percent
            if mem_usage > 90:
                logger.warning(f"[BuilderEngine] Memória em {mem_usage}%. Pausa de segurança de 30s...")
                time.sleep(30)
                return False
            return True
        except Exception as e:
            logger.error(f"[BuilderEngine] Erro ao checar saúde do sistema: {e}")
            return True # Continua mesmo se a checagem falhar

    def add_task(self, task_name, meta):
        self.task_queue.put({"name": task_name, "meta": meta})
        return f"Tarefa '{task_name}' na fila."

    def _process_tasks(self):
        while True:
            task = self.task_queue.get()
            
            # Checagem de segurança antes de iniciar
            if not self._check_system_health():
                self.task_queue.put(task) # Devolve a tarefa para o fim da fila
                continue

            try:
                self.status = f"WORKING: {task['name']}"
                file_path = task['meta'].get('path')
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code_content = f.read(50000) 
                    
                    prompt = f"Refatore o código abaixo para eficiência. Retorne APENAS o código:\n\n{code_content}"
                    novo_codigo = self._chamar_ollama(prompt)
                    
                    with open(f"{file_path}.new", 'w', encoding='utf-8') as f:
                        f.write(novo_codigo)
                    
                    logger.info(f"[BuilderEngine] Concluído: {file_path}")
                
            except Exception as e:
                logger.error(f"[BuilderEngine] Erro na tarefa {task['name']}: {e}")
            finally:
                self.status = "IDLE"
                self.task_queue.task_done()
                gc.collect() 

    def _chamar_ollama(self, prompt):
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": 2048} 
            }
            response = requests.post(self.ollama_url, json=payload, timeout=180)
            return response.json().get("response", "") if response.status_code == 200 else "# Erro Ollama"
        except Exception as e:
            logger.error(f"Erro Ollama: {e}")
            return "# Erro de comunicação"

# Instância global
builder_engine = BuilderEngine()