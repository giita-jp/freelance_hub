"""モジュールの目的：ページを最下部まで何度かスクロールして、遅延ロード（Lazy Loading） の要素（カードなど）をすべて読み込ませる

本モジュールは以下を提供します：
- `scroll_to_load(driver, rounds, sleep_sec, logger)`: ページを何度もスクロールして全てのカードを読み込む
- `wait_cards(wait, sel_card, logger): ページ遷移（URLの変化）または描画更新が落ち着くまで軽く待機する
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def scroll_to_load(driver, rounds: int = 8, sleep_sec: float = 1.0, logger=None):
    """ページを何度もスクロールして全てのカードを読み込む。

    ページの下まで何度かスクロールして、遅延ロードされる要素（例：カードや画像）を
    すべて表示させる。ページの高さが変わらなくなった時点で終了する。

    Args:
        driver (WebDriver): Selenium の WebDriver オブジェクト。
        rounds (int, optional): 最大スクロール回数。デフォルトは8。
        sleep_sec (float, optional): 各スクロール間の待機秒数。デフォルトは1.0。
        logger (Logger, optional): ログ出力用のロガー。指定しない場合はNone。

    """
    if logger:
        logger.debug(f"遅延読み込みスクロール: rounds={rounds}, sleep={sleep_sec}")
    last_height = 0
    for _ in range(rounds):
        # JavaScriptでページ最下部へスクロール
        # （window.scrollTo(x, y) → y に document.body.scrollHeight を指定すると最下部）
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(sleep_sec)
        # ページの高さを取得する
        new_height = driver.execute_script("return document.body.scrollHeight")
        # ページの高さが変わらなければ「もう新しい要素がロードされていない」と判断して終了
        if new_height == last_height:
            break
        last_height = new_height


def wait_cards(wait, sel_card: str, logger=None):
    """指定されたカード要素がDOM上に出現するまで待機する。

    ページの読み込みや遅延レンダリング（Lazy Load）によって
    要素がまだDOMに存在しない場合、この関数はそれらが出揃うまで
    Seleniumの `WebDriverWait` を使って待機する。

    Args:
        wait (WebDriverWait): SeleniumのWebDriverWaitインスタンス。
            `presence_of_all_elements_located` を利用して要素の存在を確認する。
        sel_card (str): 検出対象となるカード要素のCSSセレクタ。
        logger (optional): ログ出力用のロガー。
            指定された場合は、待機の開始と完了をデバッグログに記録する。

    Raises:
        TimeoutException: 指定時間内に要素が出現しなかった場合。

    Example:
        >>> wait_cards(wait, ".ProjectCard")
        # すべての .ProjectCard 要素が出現するまで待機
    """
    if logger:
        logger.debug("カード出揃い待機開始")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel_card)))
    if logger:
        logger.debug("カード出揃い待機完了")
