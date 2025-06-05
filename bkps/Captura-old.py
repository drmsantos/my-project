# Captura.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from io import BytesIO
import os
import time
import traceback

def main():
    def configurar_navegador():
        servico = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--force-device-scale-factor=0.75')
        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=servico, options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
        return driver

    def realizar_login(driver, wait, url_login, usuario, senha):
        driver.get(url_login)
        driver.execute_script("document.body.style.zoom='75%'")
        campo_usuario = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test-subj='user-name']")))
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)
        campo_senha = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-test-subj='password']")))
        campo_senha.clear()
        campo_senha.send_keys(senha)
        botao_login = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']")))
        botao_login.click()

    def clicar_dismiss(driver, wait):
        try:
            botao_dismiss = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Dismiss']")))
            botao_dismiss.click()
            time.sleep(2)
        except:
            print("Botão 'Dismiss' não encontrado. Continuando...")

    def remover_toasts(driver):
        script = "let toasts = document.querySelectorAll('.euiToast'); toasts.forEach(t => t.remove());"
        driver.execute_script(script)

    def acessar_dashboard(driver, wait, url_dashboard):
        driver.get(url_dashboard)
        print("Removendo notificações de erro/toasts...")
        try:
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            remover_toasts(driver)
            print("Aguardando carregamento do dashboard...")
            # Espera até que um elemento importante do dashboard apareça
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".euiPanel")) )
        except:
            print("Erro ao carregar o dashboard. Verifique a URL ou a conexão.")

    def capturar_telas(driver, lista_capturas, pasta_destino):
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            print(f"Pasta criada: {pasta_destino}")
        for item in lista_capturas:
            nome_arquivo = os.path.join(pasta_destino, item["nome_arquivo"])
            scroll_y = item["scroll_y"]
            crop_coords = item["crop_coords"]
            print(f"Capturando: {nome_arquivo} (scroll: {scroll_y})")
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(3)  # Mantém um tempo curto para garantir o carregamento
            png = driver.get_screenshot_as_png()
            imagem = Image.open(BytesIO(png))
            imagem_cropada = imagem.crop(crop_coords)
            imagem_cropada.save(nome_arquivo)
            print(f"Imagem salva: {nome_arquivo}")

    # Parâmetros fixos
    url_login = "http://192.168.15.230:5601/app/login?"
    url_dashboard = ("http://192.168.15.230:5601/app/dashboards#/view/722b74f0-b882-11e8-a6d9-e546fe2bba5f?"
                     "_g=(filters:!(),refreshInterval:(pause:!f,value:900000),time:(from:now-7d,to:now))"
                     "&_a=(description:'Analyze%20mock%20eCommerce%20orders%20and%20revenue',filters:!(),"
                     "fullScreenMode:!f,options:(hidePanelTitles:!f,useMargins:!t),query:(language:kuery,query:''),"
                     "timeRestore:!t,title:'%5BeCommerce%5D%20Revenue%20Dashboard',viewMode:view)")
    usuario = "admin"
    senha = "P@ssw0rd"
    diretorio_base = r"D:\Projetos\Automacao\Opensearch"
    pasta_destino = os.path.join(diretorio_base, "bar")
    lista_capturas = [
        {"nome_arquivo": "Captura.png", "scroll_y": 90, "crop_coords": (3, 75, 1915, 666)},
    ]

    driver = configurar_navegador()
    wait = WebDriverWait(driver, 20)

    try:
        realizar_login(driver, wait, url_login, usuario, senha)
        print("Login realizado com sucesso.")
        clicar_dismiss(driver, wait)
        acessar_dashboard(driver, wait, url_dashboard)
        capturar_telas(driver, lista_capturas, pasta_destino)
    except Exception as e:
        print(f"Erro durante a automação: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        print("Navegador fechado.")

if __name__ == "__main__":
    main()
