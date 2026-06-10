def log(*args):
    print("[PLANNER]", *args)


def plan(user_input: str):
    text = user_input.lower()

    # =========================
    # AÇÕES DIRETAS
    # =========================

    if "abrir youtube" in text:
        return {"type": "open_url", "value": "https://youtube.com"}

    if "abrir google" in text:
        return {"type": "open_url", "value": "https://google.com"}

    if "abrir spotify" in text:
        return {"type": "open_app", "value": "spotify"}

    if "desligar pc" in text:
        return {"type": "system", "value": "shutdown /s /t 0"}

    # =========================
    # AUTOMAÇÃO
    # =========================

    if "modo trabalho" in text:
        return {
            "type": "automation",
            "value": "work_mode"
        }

    # =========================
    # SEM AÇÃO
    # =========================

    return None