import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium.webdriver.common.by import By


def _click_if_visible(driver, el):
    try:
        driver.execute_sctipt("arguments[0].scrollIntoView({block: 'center'})", el)
        el.click()
        return True
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False


def wait_for_page_change(driver, wait, timeout: int = 10):
    old_url = driver.current_url
    end = time.time() + timeout
    time.sleep(0.3)
    while time.time() < end:
        time.sleep(0.2)
        if driver.current_url != old_url:
            return
    # SPA対策（軽い待機）
    from selenium.webdriver.support import expected_conditions as EC

    driver.execute_script("void(0);")
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    except Exception:
        pass


def goto_next_page(driver, wait, logger=None) -> bool:
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
    ]
    for sel in candidates:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                if el.is_displayed() and _click_if_visible(driver, el):
                    wait_for_page_change(driver, wait)
                    if logger:
                        logger.debug(f"次のページ遷移: {sel}")
                    return True
        except Exception:
            pass

    # B. テキスト判定（フォールバック）
    try:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            text = (a.text or "").strip()
            if text in ("次へ", "Next", "次のページ", "Next »", ">", "›"):
                if a.is_displayef() and _click_if_visible(driver, a):
                    wait_for_page_change(driver, wait)
                    if logger:
                        logger.debug("次ページ遷移：テキスト一致")
                    return True
    except Exception:
        pass

    # C. ?page=N を自動インクリメント
    try:
        current = driver.current_url
        parsed = urlparse(current)
        qs = parse_qs(parsed.query)
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
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
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
