import subprocess
import webbrowser
from automation.automation import run_automation
from memory.memory_manager import memory_manager


def log(*args):
    print("[EXECUTOR]", *args)


def execute(action: dict):
    """
    action = {
        "type": "open_app | open_url | automation | system",
        "value": "...",
        "meta": {}
    }
    """

    if not action:
        return "Nada para executar"

    action_type = action.get("type")
    value = action.get("value")
    meta = action.get("meta", {})

    try:
        if action_type == "open_url":
            webbrowser.open(value)
            memory_manager.register_action("open_url", {"url": value})
            return f"Abrindo {value}"

        elif action_type == "open_app":
            subprocess.Popen(value, shell=True)
            memory_manager.register_action("open_app", {"app": value})
            return f"Abrindo aplicativo"

        elif action_type == "automation":
            result = run_automation(value, meta)
            memory_manager.register_action("automation", {"name": value})
            return result

        elif action_type == "system":
            subprocess.run(value, shell=True)
            memory_manager.register_action("system_cmd", {"cmd": value})
            return "Comando executado"

        else:
            return "Tipo de ação desconhecido"

    except Exception as e:
        log("Erro:", e)
        return "Erro ao executar ação"