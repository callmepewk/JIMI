import json
import os
import threading
from datetime import datetime
from copy import deepcopy

# ==============================
# CONFIG
# ==============================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "data", "memory.json")
BACKUP_FILE = os.path.join(BASE_DIR, "data", "memory_backup.json")

MAX_HISTORY = 40
MAX_ACTIONS = 20

# ==============================
# DEFAULT STRUCTURE
# ==============================

DEFAULT_MEMORY = {
    "user_name": "",
    "preferences": [],
    "facts": [],
    "history": [],
    "context": {},
    "last_actions": [],
    "created_at": None,
    "updated_at": None
}

# ==============================
# MEMORY MANAGER
# ==============================

class MemoryManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.memory = self._load()
        self._autosave = True

    # ==============================
    # SINGLETON
    # ==============================

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    # ==============================
    # CORE LOAD/SAVE
    # ==============================

    def _log(self, *args):
        print("[MEMORY]", *args)

    def _ensure_structure(self, data):
        for key in DEFAULT_MEMORY:
            if key not in data:
                data[key] = deepcopy(DEFAULT_MEMORY[key])
        return data

    def _load(self):
        if not os.path.exists(MEMORY_FILE):
            self._log("Criando memória inicial")
            return deepcopy(DEFAULT_MEMORY)

        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            return self._ensure_structure(data)

        except Exception as e:
            self._log("Erro ao carregar memória:", e)
            return deepcopy(DEFAULT_MEMORY)

    def save(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

        self.memory["updated_at"] = datetime.now().isoformat()

        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self._log("Erro ao salvar, criando backup:", e)
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)

    def _auto_save(self):
        if self._autosave:
            self.save()

    # ==============================
    # INTERAÇÕES
    # ==============================

    def add_interaction(self, user_input, response):
        self.memory["history"].append({
            "time": datetime.now().isoformat(),
            "user": user_input,
            "jimi": response
        })

        self.memory["history"] = self.memory["history"][-MAX_HISTORY:]
        self._auto_save()

    # ==============================
    # AÇÕES
    # ==============================

    def register_action(self, action_name, metadata=None):
        self.memory["last_actions"].append({
            "time": datetime.now().isoformat(),
            "action": action_name,
            "meta": metadata or {}
        })

        self.memory["last_actions"] = self.memory["last_actions"][-MAX_ACTIONS:]
        self._auto_save()

    # ==============================
    # CONTEXTO
    # ==============================

    def set_context(self, key, value):
        self.memory["context"][key] = value
        self._auto_save()

    def get_context(self, key=None):
        if key:
            return self.memory["context"].get(key)
        return self.memory["context"]

    def clear_context(self, key=None):
        if key:
            self.memory["context"].pop(key, None)
        else:
            self.memory["context"] = {}

        self._auto_save()

    # ==============================
    # USER DATA
    # ==============================

    def set_user_name(self, name):
        if name and name != self.memory["user_name"]:
            self.memory["user_name"] = name
            self._log("Nome aprendido:", name)
            self._auto_save()

    def add_preference(self, pref):
        if pref and pref not in self.memory["preferences"]:
            self.memory["preferences"].append(pref)
            self._auto_save()

    def add_fact(self, fact):
        if fact and fact not in self.memory["facts"]:
            self.memory["facts"].append(fact)
            self._auto_save()

    # ==============================
    # EXTRAÇÃO INTELIGENTE
    # ==============================

    def extract_info(self, text):
        text = text.lower().strip()

        if "meu nome é" in text:
            name = text.split("meu nome é")[-1].strip().capitalize()
            self.set_user_name(name)

        if "eu gosto de" in text:
            pref = text.split("eu gosto de")[-1].strip()
            self.add_preference(pref)

        triggers = ["eu sou", "eu trabalho", "eu estudo", "eu moro"]
        if any(t in text for t in triggers):
            self.add_fact(text)

        playlists = [
            "reggae", "r&b", "nostalgia", "rock",
            "blues", "brazilian deluxe", "corrida",
            "nossa playlist", "eletro", "rap"
        ]

        for p in playlists:
            if p in text:
                self.set_context("last_playlist", p)

    # ==============================
    # CONTEXTO PARA IA
    # ==============================

    def get_ai_context(self):
        return {
            "name": self.memory.get("user_name"),
            "preferences": self.memory.get("preferences")[-5:],
            "facts": self.memory.get("facts")[-5:],
            "last_playlist": self.memory.get("context", {}).get("last_playlist")
        }

    # ==============================
    # LIMPEZA
    # ==============================

    def clean(self):
        self.memory["preferences"] = list(set(self.memory["preferences"]))
        self.memory["facts"] = list(set(self.memory["facts"]))
        self._auto_save()


# ==============================
# INSTÂNCIA GLOBAL
# ==============================

memory_manager = MemoryManager.get_instance()