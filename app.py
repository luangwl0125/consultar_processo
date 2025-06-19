"""
Sistema de Consulta de Processos - e-SAJ
Interface Streamlit para automação de consultas no TJ-AL
"""

import os

from functools import partial
from time import sleep
from io import BytesIO
from typing import Optional, Union

# Configuração de logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports principais
from dotenv import load_dotenv
import streamlit as st
from PIL import ImageGrab
import pyperclip

# Imports condicionais com tratamento de erro
try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("gTTS não disponível. Funcionalidade de áudio limitada.")

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    logger.warning("SpeechRecognition não disponível. Funcionalidade de voz desabilitada.")

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    sd = None
    AUDIO_AVAILABLE = False
    logger.warning("SoundDevice não disponível. Captura de áudio desabilitada.")

try:
    import pyautogui
    HEADLESS_GUI = False
except ImportError:
    pyautogui = None
    HEADLESS_GUI = True
    logger.warning("PyAutoGUI não disponível. Automação GUI desabilitada.")

# Import local
try:
    from funcao_buscar_imagens import clica_na_imagem, IMGS
except ImportError:
    logger.error("funcao_buscar_imagens não encontrada. Automação desabilitada.")
    clica_na_imagem = None
    IMGS = None

# Configurações
CONFIG = {
    "USUARIO_LOGIN": "luan",
    "SENHA_LOGIN": "123",
    "URL_ESAJ": "https://www2.tjal.jus.br/cpopg/open.do?gateway=true",
    "TIMEOUT_PADRAO": 5,
    "SAMPLE_RATE": 16000
}

class SistemaConsulta:
    """Classe principal para gerenciar o sistema de consulta."""
    
    def __init__(self):
        self.setup_session_state()
        self.carregar_configuracoes()
        
    def setup_session_state(self):
        """Inicializa variáveis de estado da sessão."""
        if "logged" not in st.session_state:
            st.session_state.logged = False
        if "consulta_ativa" not in st.session_state:
            st.session_state.consulta_ativa = False
    
    def carregar_configuracoes(self):
        """Carrega configurações do arquivo .env."""
        load_dotenv()
        self.esaj_cpf = os.getenv("ESAJ_CPF")
        self.esaj_senha = os.getenv("ESAJ_SENHA")
        
        if not self.esaj_cpf or not self.esaj_senha:
            st.error("Configure ESAJ_CPF e ESAJ_SENHA no arquivo .env antes de usar.")
            st.stop()
    
    def validar_credenciais(self, usuario: str, senha: str) -> bool:
        """Valida credenciais de login."""
        return usuario == CONFIG["USUARIO_LOGIN"] and senha == CONFIG["SENHA_LOGIN"]
    
    def falar(self, texto: str) -> None:
        """Gera áudio com gTTS e reproduz no navegador."""
        if not TTS_AVAILABLE:
            st.warning("TTS não disponível. Instale gTTS no requirements.")
            return
            
        try:
            tts = gTTS(texto, lang="pt")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf.read(), format="audio/mp3")
        except Exception as e:
            logger.error(f"Erro ao gerar áudio: {e}")
            st.warning("Não foi possível reproduzir áudio.")
    
    def ouvir_microfone(self, timeout: int = CONFIG["TIMEOUT_PADRAO"]) -> Optional[str]:
        """Captura áudio via sounddevice se disponível."""
        if not AUDIO_AVAILABLE or not SPEECH_AVAILABLE:
            return None
            
        try:
            r = sr.Recognizer()
            fs = CONFIG["SAMPLE_RATE"]
            
            audio_np = sd.rec(int(timeout * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            audio_bytes = audio_np.tobytes()
            audio_data = sr.AudioData(audio_bytes, fs, 2)
            
            return r.recognize_google(audio_data, language='pt-BR')
        except sr.UnknownValueError:
            logger.info("Áudio não reconhecido")
            return None
        except sr.RequestError as e:
            logger.error(f"Erro na API de reconhecimento: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao capturar áudio: {e}")
            return None
    
    def processar_documento(self, texto: str) -> Optional[str]:
        """Processa e valida documento (CPF)."""
        if not texto:
            return None
        dig = ''.join(filter(str.isdigit, texto))
        return dig if len(dig) == 11 else None
    
    def processar_numero_processo(self, texto: str) -> Optional[str]:
        """Processa e valida número do processo."""
        if not texto:
            return None
        dig = ''.join(filter(str.isdigit, texto))
        return dig if len(dig) == 20 else None
    
    def executar_consulta(self, valor: str, tipo: str) -> bool:
        """Executa a automação de consulta."""
        if HEADLESS_GUI or pyautogui is None or clica_na_imagem is None:
            st.error("Automação GUI não disponível neste ambiente.")
            return False
        
        try:
            logger.info(f"Iniciando consulta: {tipo} = {valor}")
            
            # Login no sistema
            clica_na_imagem("16_e_saj", pasta=IMGS)
            sleep(7)
            # CPF/CNPJ sem formatação
            cpf = ''.join(filter(str.isdigit, self.esaj_cpf))
            pyautogui.write(cpf, interval=0.1)
            pyautogui.press('tab')
            sleep(1.5)  # Aguarda o campo senha estar pronto
            pyautogui.write(self.esaj_senha, interval=0.1)
            pyautogui.press('enter')
            sleep(7)
            
            # Navegação para consulta
            pyperclip.copy(CONFIG["URL_ESAJ"])
            pyautogui.hotkey('ctrl', 't')
            sleep(1)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            sleep(5)
            
            # Seleção do tipo de consulta
            clica_na_imagem("11_consultar_por", pasta=IMGS, confidence=0.7)
            sleep(2)
            
            # Configuração baseada no tipo
            if tipo == "processo":
                imgs = ("11_numero_1", "11_numero_2")
            else:  # cpf
                imgs = ("13_documento_1", "13_documento_2")
            
            # Clica na opção correta
            for img in imgs:
                if clica_na_imagem(img, pasta=IMGS, confidence=0.7):
                    sleep(0.5)
                    pyautogui.press('tab')
                    break
            
            # Insere o valor e executa
            pyperclip.copy(valor)
            pyautogui.hotkey('ctrl', 'v')
            sleep(1)
            pyautogui.press('enter')
            
            logger.info("Consulta executada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro na automação: {e}")
            return False
    
    def interface_login(self):
        """Interface de login."""
        st.title("🔒 Login")
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            if self.validar_credenciais(user, pwd):
                st.session_state.logged = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    
    def interface_manual(self):
        """Interface de consulta manual."""
        st.header("📋 Consulta Manual")
        
        tipo_manual = st.radio(
            "Tipo de consulta:", 
            ["Número do processo", "Documento (CPF)"]
        )
        
        entrada = st.text_input("Digite o valor:")
        
        if st.button("Executar Consulta", disabled=st.session_state.consulta_ativa):
            if not entrada.strip():
                st.error("Por favor, digite um valor.")
                return
                
            modo = "processo" if tipo_manual.startswith("Número") else "cpf"
            valor = (self.processar_numero_processo(entrada)
                    if modo == "processo" else self.processar_documento(entrada))
            
            if not valor:
                st.error(f"Valor inválido para {modo}.")
                return
            
            st.session_state.consulta_ativa = True
            st.info(f"Executando consulta por {modo}: {valor}")
            self.falar(f"Executando consulta por {modo}: {valor}")
            
            try:
                sucesso = self.executar_consulta(valor, modo)
                if sucesso:
                    st.success("✅ Consulta executada com sucesso.")
                    self.falar("Consulta concluída com sucesso.")
                else:
                    st.error("❌ Falha na execução da consulta.")
                    self.falar("Falha na execução da consulta.")
            except Exception as e:
                st.error(f"❌ Erro ao executar: {e}")
                self.falar("Ocorreu um erro na consulta.")
            finally:
                st.session_state.consulta_ativa = False
    
    def interface_voz(self):
        """Interface de consulta por voz."""
        st.header("🎤 Consulta por Voz")
        
        if not AUDIO_AVAILABLE:
            st.error("Áudio não disponível neste ambiente.")
            return
        
        placeholder = st.empty()
        
        if st.button("Iniciar captura de voz", disabled=st.session_state.consulta_ativa):
            st.session_state.consulta_ativa = True
            
            try:
                # Captura tipo de consulta
                placeholder.info("Aguardando tipo de consulta (processo ou documento)...")
                self.falar("Aguardando tipo de consulta: processo ou documento.")
                
                texto_tipo = self.ouvir_microfone(5) or ""
                modo = "processo" if "processo" in texto_tipo.lower() else "cpf"
                
                placeholder.info(f"Você escolheu: {modo}. Aguardando valor...")
                self.falar(f"Você escolheu {modo}. Fale agora o valor para consulta.")
                
                # Captura valor
                texto_valor = self.ouvir_microfone(10)
                valor = (self.processar_numero_processo(texto_valor)
                        if modo == "processo" else self.processar_documento(texto_valor))
                
                if not valor:
                    placeholder.error("⚠️ Valor não reconhecido. Reinicie para tentar novamente.")
                    self.falar("Valor não reconhecido. Por favor, tente novamente.")
                    return
                
                # Confirmação
                placeholder.info(f"Valor capturado: {valor}. Diga 'consultar' para confirmar.")
                self.falar(f"Você informou {valor}. Diga consultar para confirmar.")
                
                cmd = self.ouvir_microfone(5) or ""
                if "consultar" in cmd.lower():
                    placeholder.info("Iniciando consulta...")
                    self.falar("Iniciando consulta.")
                    
                    sucesso = self.executar_consulta(valor, modo)
                    if sucesso:
                        placeholder.success("✅ Consulta concluída com sucesso.")
                        self.falar("Consulta concluída com sucesso.")
                    else:
                        placeholder.error("❌ Erro na automação. Tente novamente.")
                        self.falar("Ocorreu um erro na consulta.")
                else:
                    placeholder.warning("Comando não reconhecido. Reinicie o processo.")
                    self.falar("Comando não reconhecido. Reiniciando processo.")
                    
            except Exception as e:
                logger.error(f"Erro na interface de voz: {e}")
                placeholder.error("❌ Erro inesperado. Tente novamente.")
                self.falar("Ocorreu um erro inesperado.")
            finally:
                st.session_state.consulta_ativa = False
        elif AUDIO_AVAILABLE:
            placeholder.info("Clique em 'Iniciar captura de voz' para começar.")

def main():
    """Função principal da aplicação."""
    # Configuração da página
    st.set_page_config(
        page_title="Consulta e-SAJ", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Configuração de tela (apenas se necessário)
    if not HEADLESS_GUI:
        ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)
    
    # Inicialização do sistema
    sistema = SistemaConsulta()
    
    # Verificação de login
    if not st.session_state.logged:
        sistema.interface_login()
        st.stop()
    
    # Interface principal
    st.title("📑 Sistema de Consulta de Processos – e-SAJ")
    st.markdown("Interface manual e por voz para automatizar consultas no TJ-AL.")
    
    # Tabs da interface
    tab1, tab2 = st.tabs(["Manual", "Por Voz"])
    
    with tab1:
        sistema.interface_manual()
    
    with tab2:
        sistema.interface_voz()

if __name__ == "__main__":
    main()
