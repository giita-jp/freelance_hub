"""モジュールの目的：ページを最下部まで何度かスクロールして、遅延ロード（Lazy Loading） の要素（カードなど）をすべて読み込ませる"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def scroll_to_load(driver, rounds: int = 8, sleep_sec: float = 1.0, logger=None):
    # この関数の目的：ページを何度もスクロールして全カードを読み込む
    if logger:
        logger.debug(f"遅延読み込みスクロール: rounds={rounds}, sleep={sleep_sec}")
    last_height = 0
    for _ in range(rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        # JavaScriptでページ最下部までスクロールする
        time.sleep(sleep_sec)
        new_height = driver.execute_script("return document.body.scrollHeight")
        # ページの高さを取得して、前回と変わったかを比較
        if new_height == last_height:
            break
        # 高さが変わらなければ「もう新しい要素がロードされていない」と判断して終了
        last_height = new_height


def wait_cards(wait, sel_card: str, logger=None):
    # この関数の目的：カード要素がDOM上に現れるまで待つ
    if logger:
        logger.debug("カード出揃い待機開始")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel_card)))
    if logger:
        logger.debug("カード出揃い待機完了")
