import os
import pyautogui

# Pasta de imagens (use PNGs nomeadas conforme o script)
IMGS = os.path.join(os.path.dirname(__file__), 'IMGS')

def clica_na_imagem(nome: str, pasta: str = IMGS, confidence: float = 0.7) -> bool:
    caminho = os.path.join(pasta, f"{nome}.png")
    try:
        pos = pyautogui.locateCenterOnScreen(caminho, confidence=confidence)
        if pos:
            pyautogui.click(pos)
            return True
    except Exception:
        pass
    return False