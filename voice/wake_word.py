import re
import unicodedata
import time

# ================= CONFIG =================

WAKE_WORDS = [
    "jimi",
    "jimmy",
    "gimi",
    "gimy"
]

# distância aceitável (erro de pronúncia/transcrição)
MAX_DISTANCE = 1

# cooldown para evitar ativações seguidas
WAKE_COOLDOWN = 2.0

last_activation = 0

# ================= NORMALIZAÇÃO =================

def normalize(text: str) -> str:
    """
    Remove acentos, baixa caixa e limpa caracteres
    """
    text = text.lower()

    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")

    text = re.sub(r"[^a-z0-9\s]", "", text)

    return text

# ================= DISTÂNCIA (LEVENSHTEIN SIMPLES) =================

def levenshtein(a, b):
    if a == b:
        return 0

    if len(a) < len(b):
        return levenshtein(b, a)

    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)

    for i, c1 in enumerate(a):
        current_row = [i + 1]

        for j, c2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)

            current_row.append(min(insertions, deletions, substitutions))

        previous_row = current_row

    return previous_row[-1]

# ================= DETECÇÃO =================

def detect_wake_word(text: str) -> bool:
    global last_activation

    now = time.time()

    # cooldown
    if now - last_activation < WAKE_COOLDOWN:
        return False

    text = normalize(text)
    words = text.split()

    for word in words:
        for wake in WAKE_WORDS:

            # match direto
            if word == wake:
                last_activation = now
                return True

            # match aproximado (voz nunca é perfeita)
            if levenshtein(word, wake) <= MAX_DISTANCE:
                print(f"🔎 Aproximação detectada: {word} ~ {wake}")
                last_activation = now
                return True

    return False

# ================= EXTRA =================

def extract_command(text: str) -> str:
    """
    Remove wake word do texto e retorna comando limpo
    """
    text = normalize(text)

    for wake in WAKE_WORDS:
        text = text.replace(wake, "")

    return text.strip()

# ================= DEBUG =================

if __name__ == "__main__":
    while True:
        t = input("Você: ")

        if detect_wake_word(t):
            print("✅ Wake word detectada!")
            print("➡️ Comando:", extract_command(t))
        else:
            print("❌ Nada detectado")