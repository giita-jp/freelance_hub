"""次ページに進む（ページネーション）処理を提供するユーティリティ。

本モジュールは以下を提供します：
- `_click_if_visible(driver, el)`: 要素を画面内にスクロールして安全にクリック
- `wait_for_page_change(driver, wait, timeout)`: ページ遷移（もしくは描画更新）が完了するまで待機
- `goto_next_page(driver, wait, logger)`: 「次へ」リンクを検出して遷移、見つからなければ `?page=N` を自動インクリメント
"""

import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium.webdriver.common.by import By


def _click_if_visible(driver, el):
    """要素を画面中央付近にスクロールさせたうえでクリックする。

    まず通常の `.click()` を試み、失敗した場合は
    JavaScriptでの `arguments[0].click()` をフォールバックとして試す。

    Args:
        driver (WebDriver): Selenium の WebDriver インスタンス。
        el (WebElement): クリック対象の要素。

    Returns:
        bool: クリックできた場合は True、いずれの方法でも失敗した場合は False。

    Notes:
        - ビューポート外の要素や、ヘッダーに隠れている要素に対して
            直接 `.click()` を行うと例外になることがあるため、
            事前に `scrollIntoView({block: 'center'})` で中央へ移動します。
        - それでも失敗する場合の対策として、最後に JS クリックを試みています。
    """
    try:
        # 要素 el がブラウザ画面の中央に見えるようにスクロール
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", el)
        el.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False


def wait_for_page_change(driver, wait, timeout: int = 10):
    """ページ遷移（URLの変化）または描画更新が落ち着くまで軽く待機する。

    まず現在URLを記録し、一定時間の間に URL が変化したら遷移完了とみなす。
    SPA（Single Page Application）で URL が変わらないケースに備えて、
    最後に `presence_of_element_located(("css selector", "body"))` で
    軽い待機を行う。

    Args:
        driver (WebDriver): Selenium の WebDriver インスタンス。
        wait (WebDriverWait): Selenium の WebDriverWait インスタンス。
        timeout (int, optional): URL 変化を待つ最大秒数。デフォルト 10 秒。

    Returns:
        None

    Notes:
        - 厳密なネットワークアイドルやフレームワーク固有の
            「描画完了」を待つものではありません。実装を軽量に保つため、
            URL変化 or bodyの presence を用いた簡易待機です。
    """
    old_url = driver.current_url
    end = time.time() + timeout
    time.sleep(0.3)
    while time.time() < end:
        time.sleep(0.2)
        if driver.current_url != old_url:
            return
    # SPA(=Single Page Application)対策（軽い待機）
    from selenium.webdriver.support import expected_conditions as EC

    driver.execute_script("void(0);")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    except Exception:
        pass


def goto_next_page(driver, wait, logger=None) -> bool:
    """次ページへ遷移する。

    手順は以下の優先順で試行する：
        A) よくある「次へ」候補の CSS セレクタ群を走査し、クリック遷移
        B) aタグのテキスト（「次へ」「Next」など）一致でクリック遷移（フォールバック）
        C) 現在URLのクエリ `?page=N` を自動インクリメントして遷移（最終手段）

    いずれかで遷移できた場合は True を返す。失敗した場合は False。

    Args:
        driver (WebDriver): Selenium の WebDriver インスタンス。
        wait (WebDriverWait): Selenium の WebDriverWait インスタンス。
        logger (optional): ロガー。遷移手段や失敗時の情報を DEBUG で出力する。

    Returns:
        bool: 遷移に成功したら True、次ページが見つからない／遷移できない場合は False。

    Notes:
        - クリック遷移に成功した場合・URL書き換えで遷移した場合ともに、
            `wait_for_page_change` を呼んで軽く安定待機します。
        - 最後の C 手段（URL書き換え）は、ページャ UI が存在しない、
            あるいは検出できない場合のための保険です。
    """

    # A. 一般的な次へ候補（SeleniumのCSSとして有効なもののみ）
    candidates = [
        "a[rel='next']",
        "a[aria-label='Next']",
        "a[aria-label='次へ']",
        "button[aria-label='Next']",
        "button[aria-label='次へ']",
        ".Pagination a[rel='next']",
        ".Pagination a[aria-label='Next']",
        ".Pagination a[aria-label='次へ']",
        "a.Pagination_NextLink",
        "a.Pagination_Link.Pagination_NextLink",
    ]
    for sel in candidates:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                if el.is_displayed() and _click_if_visible(driver, el):
                    wait_for_page_change(driver, wait)
                    if logger:
                        logger.debug(f"次ページ遷移: {sel}")
                    return True
        except Exception:
            pass

    # B. テキスト判定（フォールバック）
    try:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            text = (a.text or "").strip()
            if text in ("次へ", "Next", "次のページ", "Next »", ">", "›"):
                if a.is_displayed() and _click_if_visible(driver, a):
                    wait_for_page_change(driver, wait)
                    if logger:
                        logger.debug("次ページ遷移：テキスト一致")
                    return True
    except Exception:
        pass

    # C. ?page=N を自動インクリメント
    try:
        current = driver.current_url  # 現在のURLを取得
        parsed = urlparse(
            current
        )  # URLを分解（scheme, netloc, path, params, query, fragment）
        qs = parse_qs(parsed.query)  # クエリ文字列をdict化
        # (例) qs = {"page":["3"]}
        page = 1
        if "page" in qs and qs["page"]:
            try:
                page = int(qs["page"][0])
            except ValueError:
                page = 1
        next_page = page + 1
        qs["page"] = [str(next_page)]
        new_query = urlencode(
            {k: v[0] if isinstance(v, list) else v for k, v in qs.items()}
        )
        new_url = urlunparse(
            # "https://freelance-hub.jp/project/skill/7/?page=3"の場合
            (
                parsed.scheme,  # scheme='https'
                parsed.netloc,  # netloc='freelance-hub.jp'
                parsed.path,  # path='/project/skill/7/'
                parsed.params,  # params=''
                new_query,  # query='page=3'
                parsed.fragment,  # fragment=''
            )
        )
        if new_url != current:
            driver.get(new_url)
            wait_for_page_change(driver, wait)
            if logger:
                logger.debug(f"次ページ遷移: URL書き換え -> {new_url}")
            return True
    except Exception:
        pass

    if logger:
        logger.debug("次ページなし")
    return False
