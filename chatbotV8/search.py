from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from pathlib import Path
from PIL import Image
import numpy as np
import pytesseract
import time
import cv2
import os

""" Script para capturar uma screenshot de uma página web e extrair texto dela usando OCR. 
    Requisitos:
    - Instalar o Tesseract OCR:
    - Windows: https://github.com/UB-Mannheim/tesseract/wiki
    - Após a instalação, adicione o caminho do executável do Tesseract à variável de ambiente PATH.
    
    - Instalar as bibliotecas Python necessárias:
    pip install selenium pillow pytesseract"""

# Caminho para o Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "backend" / "dados"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_screenshot(url: str) -> str:
    """ Captura uma screenshot da página web na URL fornecida e salva como imagem. """

    # Configurar o Selenium WebDriver para usar o Chrome em modo headless
    options = Options() # Configurações do Chrome
    options.add_argument("--headless=new") # Executa o Chrome em modo headless (sem interface gráfica)
    options.add_argument("--window-size=1920,1080") # Define o tamanho da janela para capturar a screenshot completa

    driver = webdriver.Chrome(options=options) # Inicializa o WebDriver do Chrome
    driver.get(url) # Navega até a URL fornecida

    time.sleep(10)  # Espera a página carregar completamente

    screenshot_path = OUTPUT_DIR / f"{normalize_url(url)}.png" # Caminho para salvar a screenshot
    driver.save_screenshot(str(screenshot_path)) # Captura e salva a screenshot
    driver.quit() # Fecha o navegador
    
    return str(screenshot_path)

def extract_text_from_image(url: str) -> None:
    """ Extrai texto de uma imagem usando OCR e salva em um arquivo .txt. """
    # Capturar a screenshot da página web
    image_path = get_screenshot(url)

    config_tesseract = f'--psm 6'

    # Normaliza o caminho da imagem para evitar problemas com caracteres especiais
    image_path = os.path.normpath(str(image_path))

    # Verifica se a imagem foi carregada corretamente
    if not os.path.exists(image_path):
        print(f"A imagem {image_path} não foi encontrada.")
        return

    # Lê a imagem usando OpenCV
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    # Converte a imagem para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Usar o pytesseract para extrair texto da imagem
    texto = pytesseract.image_to_string(gray, lang="por", config=config_tesseract).strip()

    #print("\nTexto extraído da imagem:\n")
    #print(texto)

    # Salvar o texto extraído em um arquivo .txt
    out_txt = OUTPUT_DIR / f"{normalize_url(url)}.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(texto)

    # Depois de extrair o texto, removemos a imagem para economizar espaço
    #Path(image_path).unlink() # Descomentar, faz com que a imagem seja deletada após o processamento

#TODO: Adicionar função para fazer o download do arquivo a partir do link fornecido

def normalize_url(url: str) -> str:
    return url.replace('https:', '').replace('|', '_').replace('/', '_').replace(':', '_').replace('<', '_').replace('>', '_').replace('?', '_').replace('*', '_').replace('""', '_')

if __name__ == '__main__':
    url = "https://fiapcom-my.sharepoint.com/:b:/g/personal/pf1226_fiap_com_br/EWnpZhJcRwhGv0aAy495KrwBPZEVNaURjCEbzHaOPPXMfg?e=qFrarv"
    screenshot_path = get_screenshot(url)
    extract_text_from_image(screenshot_path)