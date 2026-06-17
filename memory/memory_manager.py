import json
import os
import threading
import numpy as np
from datetime import datetime
from copy import deepcopy
from sentence_transformers import SentenceTransformer

# ==============================
# VECTOR STORE (SEMÂNTICO)
# ==============================
class VectorStore:
    def __init__(self):
        # Modelo leve para buscas semânticas locais
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.data = [] 

    def add(self, text):
        embedding = self.model.encode(text)
        self.data.append({"text": text, "embedding": embedding})

    def search(self, query, top_k=3):
        if not self.data: return []
        query_embedding = self.model.encode(query)
        results = []
        for item in self.data:
            similarity = np.dot(query_embedding, item["embedding"])
            results.append((item["text"], similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:top_k]]

# ==============================
# MEMORY MANAGER
# ==============================
class MemoryManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.vector_store = VectorStore()
        self.memory = self._load()
        self._autosave = True
        # Indexa fatos existentes na inicialização
        for fact in self.memory.get("facts", []):
            self.vector_store.add(fact)

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    # ... (Mantenha aqui os métodos _load, save, etc do seu código original) ...
    # Abaixo, as atualizações necessárias:

    def add_fact(self, fact):
        if fact and fact not in self.memory["facts"]:
            self.memory["facts"].append(fact)
            self.vector_store.add(fact) # Indexação Semântica
            self._auto_save()

    def query_facts(self, query):
        """Busca fatos relevantes sobre o Sr. Pedro usando IA"""
        return self.vector_store.search(query)

    def get_ai_context(self, query=""):
        """Retorna o contexto condensado para a LLM"""
        relevant_facts = self.query_facts(query)
        return {
            "name": self.memory.get("user_name"),
            "relevant_facts": relevant_facts,
            "last_playlist": self.memory.get("context", {}).get("last_playlist")
        }

# Instância global
memory_manager = MemoryManager.get_instance()