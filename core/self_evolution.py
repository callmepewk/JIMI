import os
import json
import subprocess
from datetime import datetime

# ================= CONFIG =================

BASE_PATH = "generated_projects"

# ================= UTIL =================

def ensure_base():
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)

def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# ================= ENGINE =================

def analyze_request(prompt: str):
    """
    Decide tipo de projeto baseado no prompt
    """

    prompt = prompt.lower()

    if "api" in prompt:
        return "backend_api"

    if "site" in prompt or "web" in prompt:
        return "web_app"

    if "automação" in prompt or "bot" in prompt:
        return "automation"

    return "generic"

# ================= GERAÇÃO =================

def generate_project_structure(project_type, name):

    path = os.path.join(BASE_PATH, name)
    os.makedirs(path, exist_ok=True)

    if project_type == "backend_api":

        with open(f"{path}/app.py", "w") as f:
            f.write("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok"}
""")

    elif project_type == "web_app":

        os.makedirs(f"{path}/frontend", exist_ok=True)

        with open(f"{path}/frontend/index.html", "w") as f:
            f.write("<h1>Projeto Web JIMI</h1>")

    elif project_type == "automation":

        with open(f"{path}/bot.py", "w") as f:
            f.write("# automação inicial")

    return path

# ================= ESTIMATIVA =================

def estimate(project_type):

    estimates = {
        "backend_api": "2 a 5 dias",
        "web_app": "3 a 10 dias",
        "automation": "1 a 3 dias",
        "generic": "depende da complexidade"
    }

    return estimates.get(project_type)

# ================= HOSPEDAGEM =================

def suggest_hosting(project_type):

    if project_type == "backend_api":
        return ["AWS", "Render", "Railway"]

    if project_type == "web_app":
        return ["Vercel", "Cloudflare Pages"]

    if project_type == "automation":
        return ["Servidor local", "Docker"]

    return ["Custom"]

# ================= EXECUTOR =================

def create_project_from_prompt(prompt):

    ensure_base()

    project_type = analyze_request(prompt)
    name = f"{project_type}_{timestamp()}"

    path = generate_project_structure(project_type, name)

    return {
        "name": name,
        "type": project_type,
        "path": path,
        "estimate": estimate(project_type),
        "hosting": suggest_hosting(project_type)
    }