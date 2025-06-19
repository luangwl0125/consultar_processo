import streamlit as st
from dotenv import load_dotenv
import os
from gtts import gTTS
from io import BytesIO
import speech_recognition as sr

# Carrega variáveis de ambiente
load_dotenv()
ESAJ_CPF = os.getenv("ESAJ_CPF")
ESAJ_SENHA = os.getenv("ESAJ_SENHA")

def falar(texto):
    """Gera áudio com gTTS e reproduz no navegador."""
    tts = gTTS(texto, lang="pt")
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    st.audio(buf.read(), format="audio/mp3")

def processar_documento(texto):
    if not texto:
        return None
    documento = ''.join(filter(str.isdigit, texto))
    if len(documento) == 11:
        return documento
    return None

def processar_numero_processo(texto):
    if not texto:
        return None
    numero = ''.join(filter(str.isdigit, texto))
    if len(numero) == 20:
        return numero
    return None

def ouvir_microfone(timeout=5):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Fale agora...")
        audio = r.listen(source, timeout=timeout, phrase_time_limit=timeout)
        try:
            texto = r.recognize_google(audio, language='pt-BR')
            return texto
        except Exception:
            return None

st.set_page_config(page_title="Consulta e-SAJ", layout="wide")
st.title("Consulta de Processos – e-SAJ (Simulação)")

tab1, tab2 = st.tabs(["Manual", "Por Voz"])

with tab1:
    st.header("Consulta Manual")
    tipo = st.radio("Tipo de consulta:", ["Número do processo", "Documento (CPF)"])
    entrada = st.text_input("Digite o valor:")
    if st.button("Processar"):
        if tipo == "Número do processo":
            valor = processar_numero_processo(entrada)
            if valor:
                st.success(f"Número do processo reconhecido: {valor}")
                falar(f"Número do processo reconhecido: {valor}")
            else:
                st.error("Número do processo inválido.")
                falar("Número do processo inválido.")
        else:
            valor = processar_documento(entrada)
            if valor:
                st.success(f"Documento reconhecido: {valor}")
                falar(f"Documento reconhecido: {valor}")
            else:
                st.error("Documento inválido.")
                falar("Documento inválido.")

with tab2:
    st.header("Consulta por Voz")
    if st.button("Iniciar captura de voz"):
        st.info("Diga 'processo' ou 'documento' para escolher o tipo.")
        texto_tipo = ouvir_microfone(5)
        if texto_tipo:
            if "processo" in texto_tipo.lower():
                modo = "processo"
            elif "documento" in texto_tipo.lower() or "cpf" in texto_tipo.lower():
                modo = "documento"
            else:
                st.error("Tipo não reconhecido.")
                falar("Tipo não reconhecido.")
                st.stop()
            st.success(f"Tipo reconhecido: {modo}")
            falar(f"Tipo reconhecido: {modo}. Fale agora o valor.")
            texto_valor = ouvir_microfone(10)
            if modo == "processo":
                valor = processar_numero_processo(texto_valor)
            else:
                valor = processar_documento(texto_valor)
            if valor:
                st.success(f"Valor reconhecido: {valor}")
                falar(f"Valor reconhecido: {valor}")
            else:
                st.error("Valor inválido.")
                falar("Valor inválido.")
        else:
            st.error("Não foi possível reconhecer o tipo.")
            falar("Não foi possível reconhecer o tipo.")

st.markdown("---")
st.info("Esta é uma simulação para uso no Streamlit Cloud. A automação real do e-SAJ só é possível localmente.")
