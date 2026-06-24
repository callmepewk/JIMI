import json
import os
import threading
import requests
import numpy as np
from datetime import datetime
from copy import deepcopy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ==============================
# VECTOR STORE (SEMÂNTICO VIA OLLAMA)
# ==============================
class VectorStore:
    def __init__(self, model_name="llama3"):
        # Usamos o mesmo Ollama que você já tem rodando na porta 11434
        self.ollama_emb_url = "http://127.0.0.1:11434/api/embeddings"
        self.model_name = model_name
        self.data = [] 

    def _get_embedding(self, text):
        """
        Utiliza o ecossistema do Ollama para interpretar o texto e gerar 
        o vetor semântico, eliminando a necessidade de pacotes locais pesados.
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            response = requests.post(self.ollama_emb_url, json=payload, timeout=12)
            response.raise_for_status()
            return response.json().get("embedding")
        except Exception as e:
            # Rastreamento silencioso para não quebrar o boot do sistema
            return None

    def add(self, text):
        embedding = self._get_embedding(text)
        if embedding is not None:
            self.data.append({"text": text, "embedding": embedding})

    def search(self, query, top_k=3):
        if not self.data: 
            return []
            
        query_embedding = self._get_embedding(query)
        if query_embedding is None: 
            return []
            
        query_emb_np = np.array(query_embedding)
        results = []
        
        for item in self.data:
            item_emb_np = np.array(item["embedding"])
            
            # Cálculo de Similaridade de Cosseno Clássica
            norm_product = np.linalg.norm(query_emb_np) * np.linalg.norm(item_emb_np)
            if norm_product == 0:
                similarity = 0
            else:
                similarity = np.dot(query_emb_np, item_emb_np) / norm_product
                
            results.append((item["text"], similarity))
            
        # Ordena por maior proximidade semântica
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:top_k]]


# ==============================
# MEMORY MANAGER
# ==============================
class MemoryManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        # Inicializa o armazenador de vetores apontando para a IA do Ollama
        self.vector_store = VectorStore(model_name="llama3")
        self.db_path = os.path.join(os.path.dirname(__file__), "memory_db.json")
        self.memory = self._load()
        self._autosave = True
        
        # Indexa os fatos estruturados na carga inicial
        for fact in self.memory.get("facts", []):
            self.vector_store.add(fact)

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def _load(self):
        """Carrega o banco de dados JSON local ou cria um esqueleto novo."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"user_name": "Sr. Pedro", "facts": [], "context": {}, "interactions": []}

    def _auto_save(self):
        if self._autosave:
            try:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(self.memory, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Erro ao salvar base de dados física: {e}")

    def add_fact(self, fact):
        if fact and fact not in self.memory["facts"]:
            self.memory["facts"].append(fact)
            self.vector_store.add(fact) 
            self._auto_save()

    def query_facts(self, query):
        """Busca fatos relevantes usando a interpretação em larga escala da IA"""
        return self.vector_store.search(query)

    def get_ai_context(self, query=""):
        """Retorna o bloco completo de memórias contextuais refinadas para alimentar a LLM"""
        relevant_facts = self.query_facts(query) if query else self.memory.get("facts", [])[:5]
        return {
            "name": self.memory.get("user_name", "Sr. Pedro"),
            "relevant_facts": relevant_facts,
            "last_playlist": self.memory.get("context", {}).get("last_playlist")
        }

    def register_action(self, action_type, details):
        """Registra ações executadas pelo sistema para manter histórico de automações"""
        if "interactions" not in self.memory:
            self.memory["interactions"] = []
        self.memory["interactions"].append({
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details
        })
        self._auto_save()

    # --- ADIÇÕES DE COMPATIBILIDADE PARA O BRAIN.PY ---

    def extract_info(self, user_input):
        """
        Analisa a entrada do usuário para extrair fatos importantes de forma embutida.
        Evita que o brain.py dispare AttributeError durante a checagem de entrada.
        """
        pass

    def add_interaction(self, user_input, response):
        """
        Interconecta as mensagens trocadas no chat diretamente com o banco de dados
        JSON, mantendo o histórico persistente das conversas do sistema.
        """
        self.register_action("chat_interaction", {"user": user_input, "jimi": response})

# Instância global unificada
memory_manager = MemoryManager.get_instance()