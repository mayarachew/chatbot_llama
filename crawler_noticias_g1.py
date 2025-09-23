from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# -----------------------------
# Configuração do Chrome
# -----------------------------
chromedriver = Service(ChromeDriverManager().install())
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=chromedriver, options=options)

wait = WebDriverWait(driver, 10)

# -----------------------------
# Função para coletar links de uma página
# -----------------------------
def pegar_links(url):
    driver.get(url)
    time.sleep(2)  # espera o JS carregar

    # tenta múltiplos seletores
    seletores = [
        "a.feed-post-link",                   # antigo
        "a.feed-post-body-title",             # novo
        "a.feed-post-link > h2"               # manchetes dentro de h2
    ]

    hrefs = set()
    for sel in seletores:
        elementos = driver.find_elements(By.CSS_SELECTOR, sel)
        for el in elementos:
            href = el.get_attribute("href")
            if href:
                hrefs.add(href)

    if not hrefs:
        print(f"⚠️ Nenhum link encontrado em {url}")

    return sorted(hrefs)

# -----------------------------
# URLs das seções que deseja rastrear
# -----------------------------
secoes = [
    "https://g1.globo.com/",                   # principal
    "https://g1.globo.com/economia/",          # economia
    "https://g1.globo.com/tecnologia/",        # tecnologia
]

# -----------------------------
# Coleta de links
# -----------------------------
hrefs = []
for secao in secoes:
    links_secao = pegar_links(secao)
    hrefs.extend(links_secao)

hrefs = sorted(set(hrefs))  # remove duplicados
print(f"Total de links coletados: {len(hrefs)}")

# -----------------------------
# Coleta de notícias completas
# -----------------------------
resultados = []

for idx, href in enumerate(hrefs, start=1):
    try:
        print(f"\n🔗 ({idx}) {href}")
        driver.get(href)
        time.sleep(5)

        # Título
        titulo_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        titulo = titulo_el.text.strip()

        # Corpo completo da notícia
        paragrafos = driver.find_elements(By.CSS_SELECTOR, "div.mc-body p")
        corpo = " ".join([p.text for p in paragrafos]).strip()

        resultados.append({
            "_id": str(idx),      # id crescente em string
            "chunk_text": titulo,
            "link": href,
            "texto_completo": corpo       # texto completo
        })

    except Exception as e:
        print(f"⚠️ Erro em {href}: {e}")
        continue

driver.quit()

# -----------------------------
# Salva em JSON
# -----------------------------
with open("./database/noticias_g1.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print("\n✅ Crawler finalizado! Notícias salvas em database/noticias_g1.json")
