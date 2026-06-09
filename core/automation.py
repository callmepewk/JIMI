import pyautogui
import subprocess
import time
import webbrowser
import os

pyautogui.PAUSE = 0.5

def execute_action(text):
    text = text.lower()

    # =========================
    # ABRIR APLICATIVOS
    # =========================
    if "abrir spotify" in text:
        try:
            subprocess.Popen("spotify")
            return "Abrindo Spotify"
        except:
            return "Não consegui abrir o Spotify"

    if "abrir navegador" in text or "abrir google" in text:
        webbrowser.open("https://google.com")
        return "Abrindo navegador"

    # =========================
    # PESQUISAR NO SPOTIFY
    # =========================
    if "tocar" in text and "spotify" in text:
        musica = text.replace("tocar", "").replace("no spotify", "").strip()

        try:
            subprocess.Popen("spotify")
            time.sleep(5)

            # CTRL + L (barra de busca spotify)
            pyautogui.hotkey("ctrl", "l")
            pyautogui.write(musica)
            pyautogui.press("enter")

            time.sleep(2)

            # ENTER para tocar primeira música
            pyautogui.press("enter")

            return f"Tocando {musica} no Spotify"

        except Exception as e:
            print(e)
            return "Erro ao tentar tocar música"

    return None