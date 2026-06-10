BLOCKED_TERMS = [
    "formatar",
    "deletar sistema",
    "apagar tudo",
    "rm -rf",
]


def is_safe(text: str) -> bool:
    text = text.lower()

    for term in BLOCKED_TERMS:
        if term in text:
            return False

    return True