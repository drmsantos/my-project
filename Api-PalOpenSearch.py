import logging
import traceback
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
from io import BytesIO
import os
import time
import tempfile
import shutil
import sys

def configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("execucao.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def obter_versao_chrome():
    try:
        resultado = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        versao = resultado.stdout.strip().split()[-1]  # Exemplo: '137.0.7151.55'
        logging.info(f"Versão do Google Chrome detectada: {versao}")
        return versao
    except Exception as e:
        logging.error(f"Erro ao obter versão do Chrome: {e}")
        return None

def configurar_navegador(user_data_dir):
    try:
        chrome_options = Options()
        
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--force-device-scale-factor=0.75')
        chrome_options.add_argument('--headless=new')  # headless moderno
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.55 Safari/537.36"
        )

        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
        chrome_options.add_experimental_option("prefs", prefs)

        # Usar o ChromeDriver fixo no caminho especificado:
        servico = Service("/home/operador/my-project/chromedriver-137/chromedriver")

        driver = webdriver.Chrome(service=servico, options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
        return driver
    except Exception as e:
        logging.error(f"Erro ao configurar o navegador: {e}")
        logging.error(traceback.format_exc())
        raise

def realizar_login(driver, wait, url_login, usuario, senha):
    driver.get(url_login)
    try:
        campo_usuario = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-test-subj='user-name']")))
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)
        campo_senha = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-test-subj='password']")))
        campo_senha.clear()
        campo_senha.send_keys(senha)
        botao_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']")))
        botao_login.click()
        logging.info("Login realizado com sucesso.")
    except Exception:
        logging.error("Erro no login: Verifique o seletor ou o tempo de espera.")
        logging.error(traceback.format_exc())
        raise

def clicar_dismiss(driver, wait):
    try:
        botao_dismiss = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Dismiss']")))
        botao_dismiss.click()
        time.sleep(2)
    except Exception as e:
        logging.warning(f"Botão 'Dismiss' não encontrado ou erro ao clicar: {e}. Continuando...")

def remover_toasts(driver):
    script = "let toasts = document.querySelectorAll('.euiToast'); toasts.forEach(t => t.remove());"
    driver.execute_script(script)

def acessar_dashboard(driver, wait, url_dashboard):
    driver.get(url_dashboard)
    logging.info("Aguardando carregamento do dashboard...")
    try:
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        remover_toasts(driver)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".euiPanel")))
        logging.info("Dashboard carregado com sucesso.")
    except Exception:
        logging.error("Erro ao acessar o dashboard. Verifique a URL ou a conexão.")
        logging.error(traceback.format_exc())
        raise

def capturar_telas(driver, wait, lista_capturas, pasta_destino):
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        logging.info(f"Pasta criada: {pasta_destino}")

    for item in lista_capturas:
        nome_arquivo = os.path.join(pasta_destino, item["nome_arquivo"])
        scroll_y = item["scroll_y"]
        crop_coords = item["crop_coords"]
        try:
            logging.info(f"Capturando: {nome_arquivo} (scroll: {scroll_y})")
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(4)  # Espera a página estabilizar um pouco mais
            png = driver.get_screenshot_as_png()
            imagem = Image.open(BytesIO(png))
            imagem_cropada = imagem.crop(crop_coords)
            imagem_cropada.save(nome_arquivo)
            logging.info(f"Imagem salva: {nome_arquivo}")
        except Exception:
            logging.error(f"Erro ao capturar imagem {nome_arquivo}:")
            logging.error(traceback.format_exc())

def main():
    configurar_logging()

    usuario = os.getenv("USUARIO_AUTOMACAO", "admin")
    senha = os.getenv("SENHA_AUTOMACAO", "P@ssw0rd")

    url_login = "http://192.168.15.230:5601/app/login?"
    url_dashboard = (
        "http://192.168.15.230:5601/app/dashboards#/view/722b74f0-b882-11e8-a6d9-e546fe2bba5f"
        "?_g=(filters:!(),refreshInterval:(pause:!f,value:900000),time:(from:now-7d,to:now))"
        "&_a=(description:'Analyze%20mock%20eCommerce%20orders%20and%20revenue',filters:!(),"
        "fullScreenMode:!f,options:(hidePanelTitles:!f,useMargins:!t),query:(language:kuery,query:''),"
        "timeRestore:!t,title:'%5BeCommerce%5D%20Revenue%20Dashboard',viewMode:view)"
    )
    diretorio_base = "/home/operador/my-project/capturas"
    pasta_destino = os.path.join(diretorio_base, "pal")
    lista_capturas = [
        {"nome_arquivo": "Captura-Pal.png", "scroll_y": 90, "crop_coords": (3, 75, 1915, 666)},
    ]

    user_data_dir = tempfile.mkdtemp(prefix="chrome-user-data-")
    driver = None

    try:
        driver = configurar_navegador(user_data_dir)
        wait = WebDriverWait(driver, 30)

        realizar_login(driver, wait, url_login, usuario, senha)
        clicar_dismiss(driver, wait)
        acessar_dashboard(driver, wait, url_dashboard)
        capturar_telas(driver, wait, lista_capturas, pasta_destino)

    except Exception:
        logging.error("Erro durante a automação:")
        logging.error(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            logging.info("Navegador fechado.")
        if user_data_dir:
            shutil.rmtree(user_data_dir, ignore_errors=True)
            logging.info(f"Diretório temporário removido: {user_data_dir}")

if __name__ == "__main__":
    main()



