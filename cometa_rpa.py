import os
import csv
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

# Diretórios e setup
script_dir = os.path.dirname(os.path.abspath(__file__))
DestinoRelatorio = os.path.join(script_dir, 'raw_data')
if not os.path.exists(DestinoRelatorio):
    os.makedirs(DestinoRelatorio)

chrome_option = webdriver.ChromeOptions()
chrome_option.add_argument('--no-sandbox')
chrome_option.add_argument('--disable-dev-shm-usage')
chrome_option.add_experimental_option("prefs", {
    "download.default_directory": DestinoRelatorio,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False,
    "profile.default_content_setting_values.notifications": 2 
})
wd_chrome = webdriver.Chrome(options=chrome_option)

def wait_for_loader_after_click(driver):
    time.sleep(2)
    try:
        if driver.find_elements(By.CSS_SELECTOR, "#loader img"):
            WebDriverWait(driver, 40).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#loader img"))
            )
    except Exception as e:
        print(f"Erro ao esperar o loader desaparecer: {e}")
    time.sleep(1)

# Rotas a consultar
routes = [
    {"origin": "Belo Horizonte - Terminal Rodoviário (MG)", "destination": "São Paulo (Rod. Tietê) (SP)"},
    {"origin": "Ribeirão Preto (SP)", "destination": "São Paulo (Rod. Tietê) (SP)"},
    {"origin": "Rio de Janeiro (Novo Rio) (RJ)", "destination": "Belo Horizonte - Terminal Rodoviário (MG)"},
]

# Datas
timestamp    = datetime.now().strftime("%d_%m_%Y_%H_%M")
data_inicial = datetime.today()
hoje         = data_inicial.date()
NUM_DIAS     = 3 
datas        = [data_inicial + timedelta(days=i) for i in range(NUM_DIAS)]

# Acessa o site
url = 'https://www.viacaocometa.com.br/'
wd_chrome.get(url)
wd_chrome.set_window_size(1392, 1104)

# Abre CSV de saída
csv_filename = os.path.join(DestinoRelatorio, f"dados_viacao_cometa_rpa_{timestamp}.csv")
with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['Origem', 'Destino', 'Data', 'Tipo de assento', 'Preco',
                  'Mensagem_rota_indisp', 'Timestamp_Scraped']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for route in routes:
        try:
            wd_chrome.get(url)
            time.sleep(5)

            # Seleciona origem
            dep = WebDriverWait(wd_chrome, 10).until(
                EC.element_to_be_clickable((By.ID, "input-departure"))
            )
            dep.click(); wait_for_loader_after_click(wd_chrome)
            dep.clear(); time.sleep(1)
            dep.send_keys(route['origin'])
            WebDriverWait(wd_chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[contains(., '{route['origin']}')]"))
            ).click()
            wait_for_loader_after_click(wd_chrome)

            # Seleciona destino
            dest = wd_chrome.find_element(By.ID, "input-destination")
            dest.click(); wait_for_loader_after_click(wd_chrome)
            dest.clear(); dest.send_keys(route['destination'])
            WebDriverWait(wd_chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[contains(., '{route['destination']}')]"))
            ).click()
            wait_for_loader_after_click(wd_chrome)

            # Define datas de ida e volta apenas para inicializar a busca
            date_in = wd_chrome.find_element(By.ID, "input-date")
            date_in.click(); wait_for_loader_after_click(wd_chrome)
            date_in.clear()
            date_in.send_keys(datas[0].strftime("%d/%m/%Y"))
            date_in.send_keys(Keys.ENTER)
            time.sleep(1)

            date_rt = wd_chrome.find_element(By.ID, "input-date-return")
            date_rt.click(); wait_for_loader_after_click(wd_chrome)
            date_rt.clear()
            date_rt.send_keys(datas[-1].strftime("%d/%m/%Y"))
            date_rt.send_keys(Keys.ENTER)
            time.sleep(1)

            # Dispara a busca
            wd_chrome.find_element(By.ID, "search-button").click()
            wait_for_loader_after_click(wd_chrome)

            # Verifica se rota indisponível no carregamento inicial
            try:
                msg = wd_chrome.find_element(
                    By.CSS_SELECTOR, "span.message-val[data-js='message-validation']"
                ).text.strip()
                if "Não existe serviço para o trecho e/ou data selecionados." in msg:
                    writer.writerow({
                        'Origem': route['origin'],
                        'Destino': route['destination'],
                        'Data': '',
                        'Tipo de assento': '',
                        'Preco': '',
                        'Mensagem_rota_indisp': msg,
                        'Timestamp_Scraped': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print(f"Rota indisponível {route['origin']} -> {route['destination']}")
                    continue
            except:
                pass

            # Loop em todas as datas, incluindo hoje
            for data in datas:
                date_str = f"{data.day}/{data.month}"
                if data.date() == hoje:
                    print(f"[INFO] Extraindo ofertas para hoje ({date_str}) sem novo clique.")
                else:
                    xpath = (
                        f"//div[@data-js='date' "
                        f"and contains(text(), '{date_str}') "
                        f"and not(contains(@class,'selected'))]"
                    )
                    try:
                        elem = WebDriverWait(wd_chrome, 10).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        elem.click()
                        wait_for_loader_after_click(wd_chrome)
                    except TimeoutException:
                        print(f"[WARN] Data não clicável: {date_str}. Pulando.")
                        continue

                # Verifica indisponibilidade nesta data
                try:
                    msg = wd_chrome.find_element(
                        By.CSS_SELECTOR, "span.message-val[data-js='message-validation']"
                    ).text.strip()
                    if "Não existe serviço para o trecho e/ou data selecionados." in msg:
                        writer.writerow({
                            'Origem': route['origin'],
                            'Destino': route['destination'],
                            'Data': data.strftime('%d/%m/%Y'),
                            'Tipo de assento': '',
                            'Preco': '',
                            'Mensagem_rota_indisp': msg,
                            'Timestamp_Scraped': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        print(f"Rota indisponível em {date_str} para {route['origin']} -> {route['destination']}")
                        continue
                except:
                    pass

                # Coleta ofertas
                WebDriverWait(wd_chrome, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@data-js, 'offer-element')]"))
                )
                ofertas = wd_chrome.find_elements(By.XPATH, "//li[contains(@data-js, 'offer-element')]")
                for oferta in ofertas:
                    try:
                        tipo = oferta.find_element(
                            By.XPATH, ".//span[contains(@class, 'classtypeLabel')]"
                        ).text.strip()
                        inteiro = oferta.find_element(
                            By.XPATH, ".//span[@data-js='priceLabel']"
                        ).text.strip()
                        dec = oferta.find_element(
                            By.XPATH, ".//span[@data-js='decimalLabel']"
                        ).text.strip()
                        preco = f"R${inteiro}{dec}"
                        writer.writerow({
                            'Origem': route['origin'],
                            'Destino': route['destination'],
                            'Data': data.strftime('%d/%m/%Y'),
                            'Tipo de assento': tipo,
                            'Preco': preco,
                            'Mensagem_rota_indisp': '',
                            'Timestamp_Scraped': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception as e:
                        print(f"Erro oferta {date_str}: {e}")

            time.sleep(2)

        except Exception as e:
            print(f"Erro na rota {route['origin']} -> {route['destination']}: {e}")
            continue

wd_chrome.quit()
