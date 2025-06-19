import os
from functools import partial
from time import sleep
from dotenv import load_dotenv
import streamlit as st
from PIL import ImageGrab
import pyautogui
import pyperclip
import speech_recognition as sr

from funcao_buscar_imagens import clica_na_imagem, IMGS

# --- Configuração de login ---
if "logged" not in st.session_state:
    st.session_state.logged = False

def login():
    st.title("🔒 Login")
    user = st.text_input("Usuário")
    pwd  = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "luan" and pwd == "123":
            st.session_state.logged = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

if not st.session_state.logged:
    login()
    st.stop()

# --- Resto do app (após login) ---
# Configurações iniciais
BASE_DIR = os.path.dirname(__file__)
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)
load_dotenv()
ESAJ_CPF   = os.getenv("ESAJ_CPF")
ESAJ_SENHA = os.getenv("ESAJ_SENHA")
if not ESAJ_CPF or not ESAJ_SENHA:
    st.error("Configure ESAJ_CPF e ESAJ_SENHA no arquivo .env antes de usar.")
    st.stop()

# Reconhecimento de voz
def ouvir_microfone(timeout: int = 10) -> str | None:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=timeout)
            return recognizer.recognize_google(audio, language='pt-BR')
        except Exception:
            return None

# Processamento de entradas
def processar_documento(texto: str) -> str | None:
    digitos = ''.join(filter(str.isdigit, texto or ''))
    return digitos if len(digitos) == 11 else None

def processar_numero_processo(texto: str) -> str | None:
    digitos = ''.join(filter(str.isdigit, texto or ''))
    return digitos if len(digitos) == 20 else None

# Automação de consulta
def executar_consulta(valor: str, tipo: str) -> None:
    clica_na_imagem("16_e_saj", pasta=IMGS)
    sleep(7)
    pyautogui.write(ESAJ_CPF, interval=0.1); pyautogui.press('tab'); sleep(1)
    pyautogui.write(ESAJ_SENHA, interval=0.1); pyautogui.press('enter'); sleep(7)
    pyperclip.copy('https://www2.tjal.jus.br/cpopg/open.do?gateway=true')
    pyautogui.hotkey('ctrl', 't'); sleep(1)
    pyautogui.hotkey('ctrl', 'v'); pyautogui.press('enter'); sleep(5)
    clica_na_imagem("11_consultar_por", pasta=IMGS, confidence=0.7); sleep(2)
    key = "1" if tipo == "processo" else "3"
    imgs = ("11_numero_1","11_numero_2") if key=="1" else ("13_documento_1","13_documento_2")
    for img in imgs:
        if clica_na_imagem(img, pasta=IMGS, confidence=0.7):
            sleep(0.5); pyautogui.press('tab'); break
    pyperclip.copy(valor); pyautogui.hotkey('ctrl','v'); sleep(1); pyautogui.press('enter')

# Interface principal
st.set_page_config(page_title="Consulta e-SAJ", layout="wide")
st.title("📑 Sistema de Consulta de Processos - e-SAJ")
st.markdown("Sistema automatizado com interface por voz e manual para TJ-AL.")

tab1, tab2 = st.tabs(["Manual", "Por Voz"])

with tab1:
    st.header("Consulta Manual")
    tipo_manual = st.radio("Tipo de consulta:", ["Número do processo", "Documento (CPF)"])
    entrada = st.text_input("Digite o valor:")
    if st.button("Executar Consulta Manual"):
        modo = "processo" if tipo_manual.startswith("Número") else "cpf"
        valor = processar_numero_processo(entrada) if modo=="processo" else processar_documento(entrada)
        if not valor:
            st.error(f"Valor inválido para {modo}.")
        else:
            st.info(f"Executando consulta por {modo}: {valor}")
            try:
                executar_consulta(valor, modo)
                st.success("Consulta executada com sucesso.")
            except Exception as e:
                st.error(f"Erro ao executar: {e}")

with tab2:
    st.header("Consulta por Voz")
    placeholder = st.empty()
    if st.button("Iniciar captura de voz"):
        placeholder.info("Aguardando comando: tipo de consulta (processo ou documento)...")
        texto_tipo = ouvir_microfone(10) or ""
        modo = "processo" if any(k in texto_tipo.lower() for k in ["processo","número"]) else "cpf"
        placeholder.info(f"Você escolheu: {modo}. Aguardando valor...")
        texto_valor = ouvir_microfone(30)
        valor = processar_numero_processo(texto_valor) if modo=="processo" else processar_documento(texto_valor)
        if not valor:
            placeholder.error("Valor não reconhecido. Reinicie para tentar novamente.")
        else:
            placeholder.info(f"Valor capturado: {valor}. Diga 'consultar' para confirmar...")
            cmd = ouvir_microfone(10) or ""
            if "consultar" in cmd.lower():
                placeholder.info("Iniciando consulta...")
                try:
                    executar_consulta(valor, modo)
                    placeholder.success("Consulta concluída com sucesso.")
                except Exception:
                    placeholder.error("Erro na automação. Tente novamente.")
            else:
                placeholder.warning("Comando não reconhecido. Reinicie o processo.")
    else:
        placeholder.info("Clique em 'Iniciar captura de voz' para começar.")
