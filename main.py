from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from logger import get_logger

# URL
url = "https://freelance-hub.jp/project/skill/7/"
logger = get_logger()

try:
    logger.debug("chrome立ち上げ、開始")
    # Chrome起動
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)
    driver.get(url)
    logger.debug("chrome立ち上げ、完了")
except Exception as e:
    logger.error(f"chrome立ち上げ、失敗: \n{e}")
    raise

try:
    logger.debug("h3取得まで待機、開始")
    # 案件タイトルのh3が出るまで待機
    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.ProjectCard_Title"))
    )
    logger.debug("h3取得まで待機、完了")
except Exception as e:
    logger.error(f"h3取得まで待機、失敗: \n{e}")
    raise

titles = driver.find_elements(By.CSS_SELECTOR, "h3.ProjectCard_Title")
try:
    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.ProjectDetail_Cta"))
    )
except Exception:
    logger.debug("ProjectDetail_Cta が見つからないので、タイトル内リンクを探します")

links = driver.find_elements(By.CSS_SELECTOR, "a.ProjectDetail_Cta")
if not links:
    # フォールバック：タイトルに付いている a やカード内の project リンクを探す
    links = driver.find_elements(
        By.CSS_SELECTOR, "h3.ProjectCard_Title a, .ProjectCard a[href*='/project/']"
    )

logger.debug(f"titles={len(titles)}, links={len(links)}")

projects = []
for t, l in zip(titles, links):
    projects.append(
        {"title": t.text.strip(), "link": urljoin(url, l.get_attribute("href"))}
    )


driver.quit()
try:
    logger.debug("出力、開始")
    # 出力確認
    for p in projects:
        print(p)
    logger.debug("出力、完了")
except Exception as e:
    logger.error("出力、失敗")
    raise
