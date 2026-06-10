import pyautogui
import subprocess
import time
import webbrowser
import os
import requests
import datetime

pyautogui.PAUSE = 0.3

# =========================
# CONFIGURAÇÕES
# =========================
HOME_ASSISTANT_URL = "http://localhost:8123"  # muda quando tiver HA
HOME_ASSISTANT_TOKEN = "SEU_TOKEN_AQUI"

MEMORY = []

# =========================
# VOZ / RESPOSTA
# =========================
def speak_response(text):
    print(f"JIMI: {text}")
    return text

# =========================
# SISTEMA
# =========================
def open_app(app_name):
    try:
        subprocess.Popen(app_name)
        return True
    except:
        return False

def shutdown_pc():
    os.system("shutdown /s /t 1")

def restart_pc():
    os.system("shutdown /r /t 1")

def open_folder(path):
    try:
        os.startfile(path)
        return True
    except:
        return False

# =========================
# CONTROLES DE MÍDIA
# =========================
def control_volume(action):
    if action == "aumentar":
        pyautogui.press("volumeup", presses=5)
    elif action == "diminuir":
        pyautogui.press("volumedown", presses=5)
    elif action == "mutar":
        pyautogui.press("volumemute")

def control_media(action):
    if action == "pausar":
        pyautogui.press("playpause")
    elif action == "proxima":
        pyautogui.press("nexttrack")
    elif action == "anterior":
        pyautogui.press("prevtrack")

# =========================
# HOME ASSISTANT (ROBUSTO)
# =========================
def home_assistant_call(domain, service, entity_id):
    try:
        url = f"{HOME_ASSISTANT_URL}/api/services/{domain}/{service}"
        headers = {
            "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            url,
            headers=headers,
            json={"entity_id": entity_id},
            timeout=3
        )

        return response.status_code == 200
    except Exception as e:
        print("Erro HA:", e)
        return False

# =========================
# ALEXA (fallback por voz)
# =========================
def speak_to_alexa(command):
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(f"Alexa, {command}")
    engine.runAndWait()

# =========================
# PESQUISA INTELIGENTE
# =========================
def smart_search(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        data = requests.get(url, timeout=3).json()

        if data.get("Abstract"):
            return data["Abstract"]

        if data.get("RelatedTopics"):
            return data["RelatedTopics"][0].get("Text", "Sem resultado")

        return "Não encontrei nada relevante"
    except:
        return "Erro na pesquisa"

# =========================
# CONTEXTO / MEMÓRIA
# =========================
def remember(user_input, response):
    MEMORY.append({
        "time": datetime.datetime.now(),
        "input": user_input,
        "response": response
    })

# =========================
# INTENTS (COMANDOS)
# =========================
def execute_intent(text):
    text = text.lower()

    # -------------------------
    # APPS
    # -------------------------
    if "abrir spotify" in text:
        return speak_response("Abrindo Spotify") if open_app("spotify") else "Erro"
     
    if "abrir youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Abrindo YouTube"

    if "abrir navegador" in text or "abrir google" in text:
        webbrowser.open("https://google.com")
        return "Abrindo navegador"

    if "abrir whatsapp" in text:
        webbrowser.open("https://web.whatsapp.com")
        return "Abrindo WhatsApp"

    if "abrir vscode" in text:
        return speak_response("Abrindo VS Code") if open_app("code") else "Erro"

    # -------------------------
    # PESQUISA
    # -------------------------
    if text.startswith("pesquisar"):
        termo = text.replace("pesquisar", "").strip()
        resposta = smart_search(termo)
        return resposta

    # -------------------------
    # SPOTIFY AUTO
    # -------------------------
# =========================
# CONTEXTO GLOBAL
# =========================
CONTEXT = {
    "waiting_spotify": False,
    "spotify_mode": None
}

# =========================
# PLAYLISTS DO USUÁRIO
# =========================
PLAYLISTS = {
    "reggae": "Reggae",
    "r&b": "R&B",
    "nostalgia": "Nostalgia",
    "rock": "Rock",
    "blues": "Blues",
    "brazilian": "Brazilian Deluxe",
    "corrida": "Corrida",
    "nossa playlist": "Nossa Playlist",
    "eletro": "Eletro",
    "repê": "Rap",
    "rap": "Rap"
}

def open_spotify_and_search(query):
    try:
        subprocess.Popen("spotify")
        time.sleep(4)

        pyautogui.hotkey("ctrl", "l")
        pyautogui.write(query)
        pyautogui.press("enter")

        time.sleep(2)
        pyautogui.press("enter")

        return f"Tocando {query}"
    except:
        return "Erro ao usar Spotify"

# =========================
# INTERPRETAÇÃO INTELIGENTE
# =========================
def handle_spotify(text):

    text = text.lower()

    # =====================
    # STEP 1 - ATIVAÇÃO
    # =====================
    if "spotify" in text or "tocar" in text:
        
        # detectar se já veio algo junto
        comando = text.replace("tocar", "").replace("no spotify", "").strip()

        # PLAYLIST DIRETA
        for key in PLAYLISTS:
            if key in comando:
                return open_spotify_and_search(PLAYLISTS[key])

        # ARTISTA / MUSICA
        if comando:
            return open_spotify_and_search(comando)

        # PERGUNTA
        CONTEXT["waiting_spotify"] = True
        CONTEXT["spotify_mode"] = "general"
        return "O que você quer ouvir? Playlist, artista ou música?"

    # =====================
    # STEP 2 - RESPOSTA DO USUÁRIO
    # =====================
    if CONTEXT["waiting_spotify"]:
        CONTEXT["waiting_spotify"] = False

        # PLAYLIST
        for key in PLAYLISTS:
            if key in text:
                return open_spotify_and_search(PLAYLISTS[key])

        # ARTISTA OU MUSICA
        return open_spotify_and_search(text)

    return None
    # -------------------------
    # VOLUME / MIDIA
    # -------------------------
    if "aumentar volume" in text:
        control_volume("aumentar")
        return "Volume aumentado"

    if "diminuir volume" in text:
        control_volume("diminuir")
        return "Volume diminuído"

    if "mutar" in text:
        control_volume("mutar")
        return "Volume mutado"

    if "pausar" in text:
        control_media("pausar")
        return "Pausando"

    # -------------------------
    # SISTEMA
    # -------------------------
    if "desligar computador" in text:
        shutdown_pc()
        return "Desligando"

    if "reiniciar computador" in text:
        restart_pc()
        return "Reiniciando"

    # -------------------------
    # PASTAS
    # -------------------------
    if "abrir downloads" in text:
        return "Abrindo downloads" if open_folder(os.path.expanduser("~/Downloads")) else "Erro"

    # -------------------------
    # CASA INTELIGENTE
    # -------------------------
    if "ligar luz" in text:
        if home_assistant_call("light", "turn_on", "light.quarto"):
            return "Luz ligada"
        else:
            speak_to_alexa("ligar luz do quarto")
            return "Tentando via Alexa"

    if "desligar luz" in text:
        if home_assistant_call("light", "turn_off", "light.quarto"):
            return "Luz desligada"
        else:
            speak_to_alexa("desligar luz do quarto")
            return "Tentando via Alexa"

    # -------------------------
    # MODOS INTELIGENTES
    # -------------------------
    if "modo foco" in text:
        control_volume("mutar")
        webbrowser.open("https://www.youtube.com/results?search_query=rock")
        return "Modo foco ativado"

    if "modo trabalho" in text:
        open_app("code")
        webbrowser.open("https://github.com")
        return "Modo trabalho ativado"

    if "modo descanso" in text:
        control_media("pausar")
        return "Modo descanso ativado"

    return None

# =========================
# CÉREBRO PRINCIPAL
# =========================
def execute_action(text):
    action = execute_intent(text)

    if action:
        remember(text, action)
        return action

    # fallback inteligente
    resposta = smart_search(text)
    remember(text, resposta)

    return resposta