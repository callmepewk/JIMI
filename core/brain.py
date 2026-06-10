import requests
import json
import os
import subprocess
import webbrowser
from datetime import datetime

from jimi.automation import execute_action

# ==============================
# CONFIG
# ==============================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"
TIMEOUT = 120

MEMORY_FILE = "data/memory.json"
PROJECTS_DIR = "projects/"
TASKS_FILE = "data/tasks.json"

DEBUG = True
ACTION_MODE = True

# ==============================
# LOG
# ==============================

def log(*args):
    if DEBUG:
        print("[JIMI]", *args)

# ==============================
# JSON UTILS
# ==============================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ==============================
# MEMORY
# ==============================

memory = load_json(MEMORY_FILE, {
    "history": [],
    "skills": [],
    "projects": []
})

tasks = load_json(TASKS_FILE, [])

# ==============================
# LLM
# ==============================

def ask_llm(prompt):
    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=TIMEOUT
        )
        return res.json().get("response", "").strip()
    except Exception as e:
        log("LLM erro:", e)
        return None

# ==============================
# PLANNER (CÉREBRO REAL)
# ==============================

def plan_task(user_input):
    prompt = f"""
Você é um sistema de planejamento de IA.

Objetivo do usuário:
{user_input}

Responda em JSON com:
- type: (action, code, project, answer)
- steps: lista de etapas
- tools: quais ferramentas usar
- output: o que gerar
"""

    response = ask_llm(prompt)

    try:
        return json.loads(response)
    except:
        return {"type": "answer", "steps": [], "output": response}

# ==============================
# CODE GENERATOR
# ==============================

def generate_code(spec):
    prompt = f"""
Crie código completo baseado nisso:

{spec}

Regras:
- Código funcional
- Estrutura profissional
- Pode incluir múltiplos arquivos
- Inclua comentários
- Código limpo, sem emojis
"""

    return ask_llm(prompt)

def save_code(project_name, code):
    path = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "main.py")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    return file_path

# ==============================
# PROJECT BUILDER
# ==============================

def build_project(user_input):
    log("Criando projeto...")

    code = generate_code(user_input)

    name = f"project_{int(datetime.now().timestamp())}"
    path = save_code(name, code)

    memory["projects"].append({
        "name": name,
        "path": path,
        "created": datetime.now().isoformat()
    })

    save_json(MEMORY_FILE, memory)

    return f"Projeto criado em {path}"

# ==============================
# SELF UPGRADE 
# ==============================

def self_improve(user_input):
    prompt = f"""
Você é uma IA que melhora seu próprio código.

Baseado nisso:
{user_input}

Sugira melhorias estruturais no sistema JIMI.
Retorne código Python atualizado se necessário.
"""

    improvement = ask_llm(prompt)

    # salva sugestão
    with open("self_update_log.txt", "a", encoding="utf-8") as f:
        f.write("\n\n" + improvement)

    return "Sugestões de melhoria registradas."

# ==============================
# DEPLOY SUGGESTION
# ==============================

def suggest_deploy(project_type):
    if "web" in project_type:
        return "Sugestão: Vercel, Cloudflare Pages, Render"
    if "api" in project_type:
        return "Sugestão: AWS, Railway, Render"
    if "app" in project_type:
        return "Sugestão: Electron ou Flutter + AWS backend"
    return "Deploy genérico: Docker + VPS"

# ==============================
# TASK EXECUTION
# ==============================

def execute_plan(plan, user_input):
    t = plan.get("type")

    if t == "action":
        return execute_action(user_input)

    if t == "code":
        code = generate_code(user_input)
        return code[:500]

    if t == "project":
        result = build_project(user_input)
        deploy = suggest_deploy(user_input)
        return f"{result}\n{deploy}"

    return plan.get("output")

# ==============================
# FALLBACK
# ==============================

def fallback(user_input):
    if "oi" in user_input.lower():
        return "Fala, Senhor."
    return "Não entendi."

# ==============================
# MAIN THINK
# ==============================

def think(user_input):
    if not user_input:
        return "Sim, Senhor?"

    log("INPUT:", user_input)

    # 1. automação direta
    try:
        auto = execute_action(user_input)
        if auto:
            return auto
    except Exception as e:
        log("Erro automação:", e)

    # 2. planejamento inteligente
    plan = plan_task(user_input)

    log("PLANO:", plan)

    # 3. execução
    response = execute_plan(plan, user_input)

    if not response:
        response = fallback(user_input)

    # 4. memória
    memory["history"].append({
        "time": datetime.now().isoformat(),
        "user": user_input,
        "response": response
    })

    memory["history"] = memory["history"][-50:]
    save_json(MEMORY_FILE, memory)

    return response