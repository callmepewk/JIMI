import requests
import json
import os
import webbrowser
import subprocess
from datetime import datetime

# ==============================
# CONFIG
# ==============================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3:8b-instruct-q4_0"
TIMEOUT = 60

MEMORY_FILE = "data/memory.json"
PROFILE_FILE = "data/profile.json"

MAX_HISTORY = 6

DEBUG = True

# ==============================
# AUTOMAÇÃO
# ==============================

ACTION_MODE = True

KNOWN_APPS = {
    "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "explorer": "explorer.exe"
}

# ==============================
# MEMÓRIA
# ==============================

def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            # 🔥 garante estrutura correta
            for key in default:
                if key not in data:
                    data[key] = default[key]

            return data

    except Exception as e:
        print("Erro ao carregar JSON:", e)
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

memory = load_json(MEMORY_FILE, {
    "user_name": "",
    "preferences": [],
    "history": []
})
# 🔥 AUTO-CORREÇÃO DA MEMÓRIA
if "history" not in memory:
    memory["history"] = []

if "user_name" not in memory:
    memory["user_name"] = ""

if "preferences" not in memory:
    memory["preferences"] = []

profile = load_json(PROFILE_FILE, {
    "personality": "direto, inteligente, útil"
})

# ==============================
# CONTEXTO
# ==============================

conversation_history = []

def update_memory(user_input, response):
    try:
        if "history" not in memory or not isinstance(memory["history"], list):
            memory["history"] = []

        memory["history"].append({
            "time": datetime.now().isoformat(),
            "user": user_input,
            "jimi": response
        })

        memory["history"] = memory["history"][-20:]

        save_json(MEMORY_FILE, memory)

    except Exception as e:
        print("Erro ao salvar memória:", e)
# ==============================
# INTENT
# ==============================

def extract_intent(text):
    text = text.lower()

    if "abrir" in text:
        for app in KNOWN_APPS:
            if app in text:
                return {"type": "open", "target": app}

        if "youtube" in text:
            return {"type": "open", "target": "https://youtube.com"}

    if "pesquisar" in text or "buscar" in text:
        query = text.replace("pesquisar", "").replace("buscar", "").strip()
        return {"type": "search", "value": query}

    return None

def execute_intent(intent):
    if not intent or not ACTION_MODE:
        return None

    try:
        if intent["type"] == "open":
            target = intent["target"]

            if target in KNOWN_APPS:
                subprocess.Popen(KNOWN_APPS[target])
                return f"Abrindo {target}"

            if target.startswith("http"):
                webbrowser.open(target)
                return "Abrindo navegador"

        if intent["type"] == "search":
            url = f"https://www.google.com/search?q={intent['value']}"
            webbrowser.open(url)
            return f"Pesquisando {intent['value']}"

    except Exception as e:
        return f"Erro na ação: {e}"

    return None

# ==============================
# LLM CHECK
# ==============================

def ollama_online():
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return True
    except:
        return False

# ==============================
# PROMPT
# ==============================

def build_prompt(user_input):
    conversation_history.append(f"Usuário: {user_input}")
    conversation_history[:] = conversation_history[-MAX_HISTORY:]

    history = "\n".join(conversation_history)

    return f"""
Você é JIMI.
Responda curto, direto, em português.

{history}
Jimi:
"""

# ==============================
# FALLBACK (SEM IA)
# ==============================

def fallback_response(user_input):
    text = user_input.lower()

    if "oi" in text:
        return "E aí."

    if "tudo bem" in text:
        return "Tudo certo."

    return "Não consegui pensar direito agora."

# ==============================
# LLM
# ==============================

def perguntar_llm(prompt):
    if not ollama_online():
        return None

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=TIMEOUT
        )

        if DEBUG:
            print("STATUS:", response.status_code)

        if response.status_code != 200:
            if DEBUG:
                print(response.text)
            return None

        data = response.json()

        if DEBUG:
            print("RESPOSTA RAW:", data)

        resposta = data.get("response", "").strip()

        return resposta if resposta else None

    except Exception as e:
        print("Erro LLM:", e)
        return None

# ==============================
# COMANDOS
# ==============================

def handle_commands(text):
    text = text.lower()

    if "hora" in text:
        return f"Agora são {datetime.now().strftime('%H:%M')}"

    if "meu nome é" in text:
        name = text.split("meu nome é")[-1].strip().capitalize()
        memory["user_name"] = name
        save_json(MEMORY_FILE, memory)
        return f"Ok, {name}"

    return None

# ==============================
# MAIN
# ==============================

def think(user_input):
    if not user_input:
        return "Sim?"

    # 1. automação
    intent = extract_intent(user_input)
    action = execute_intent(intent)
    if action:
        return action

    # 2. comandos
    cmd = handle_commands(user_input)
    if cmd:
        return cmd

    # 3. IA
    prompt = build_prompt(user_input)
    resposta = perguntar_llm(prompt)

    if not resposta:
        resposta = fallback_response(user_input)

    conversation_history.append(f"Jimi: {resposta}")
    update_memory(user_input, resposta)

    return resposta