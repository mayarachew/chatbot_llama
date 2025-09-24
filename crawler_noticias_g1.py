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

    seletores = [
        "a.feed-post-link",
        "a.feed-post-body-title",
        "a.feed-post-link > h2"
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
    "https://g1.globo.com/",
    "https://g1.globo.com/economia/",
    "https://g1.globo.com/tecnologia/",
    "https://g1.globo.com/politica/",
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

        # Espera título
        titulo_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        titulo = titulo_el.text.strip()

        # Coleta corpo
        paragrafos = driver.find_elements(By.CSS_SELECTOR, "div.mc-article-body p")
        corpo = " ".join([p.text for p in paragrafos if p.text.strip()])

        if not corpo:
            print(f"⚠️ Corpo não encontrado em {href}")

        resultados.append({
            "_id": str(idx),
            "chunk_text": titulo,
            "link": href,
            "texto_completo": corpo
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
