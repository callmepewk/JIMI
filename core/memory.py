import json
import os
from datetime import datetime

# ==============================
# CONFIG
# ==============================

MEMORY_FILE = "data/memory.json"

DEFAULT_MEMORY = {
    "user_name": "",
    "preferences": [],
    "facts": [],
    "history": []
}

# ==============================
# CORE IO
# ==============================

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return DEFAULT_MEMORY.copy()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_MEMORY.copy()


def save_memory(memory):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


memory = load_memory()

# ==============================
# ATUALIZAÇÃO DE MEMÓRIA
# ==============================

def add_interaction(user_input, response):
    memory["history"].append({
        "time": datetime.now().isoformat(),
        "user": user_input,
        "jimi": response
    })

    # mantém leve
    memory["history"] = memory["history"][-30:]

    save_memory(memory)

# ==============================
# EXTRAÇÃO INTELIGENTE
# ==============================

def extract_info(text):
    text = text.lower()

    # nome
    if "meu nome é" in text:
        name = text.split("meu nome é")[-1].strip().capitalize()
        memory["user_name"] = name
        print(f"🧠 Aprendi nome: {name}")

    # gostos
    if "eu gosto de" in text:
        pref = text.split("eu gosto de")[-1].strip()

        if pref and pref not in memory["preferences"]:
            memory["preferences"].append(pref)
            print(f"🧠 Novo gosto aprendido: {pref}")

    # fatos gerais
    if any(x in text for x in ["eu sou", "eu trabalho com", "eu estudo"]):
        memory["facts"].append(text)

    save_memory(memory)

# ==============================
# CONTEXTO
# ==============================

def get_context():
    return {
        "name": memory.get("user_name"),
        "preferences": memory.get("preferences"),
        "facts": memory.get("facts")[-5:]
    }