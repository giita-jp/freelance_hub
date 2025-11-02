"""このモジュールの目的：次ページに進む（ページネーション）処理"""

import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium.webdriver.common.by import By


def _click_if_visible(driver, el):
    # この関数の目的：ページ上の要素（リンクやボタン）を安全にクリックする
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
    # この関数の目的：ページ遷移が完了するまで待つ
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
    # この関数の目的：「次ページ」を探してクリック、またはURLを書き換えて進む

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
                new_query,  # query='page=3
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
