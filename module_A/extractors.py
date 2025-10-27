from typing import Optional, Tuple
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from module_A.constants import PATTERN_ENTRY, PATTERN_DETAIL, SEL_ANCHORS_IN_CARD


def find_entry_in_card(card, base_url: str) -> Tuple[Optional[str], Optional[str]]:
    anchors = card.find_elements(By.CSS_SELECTOR, SEL_ANCHORS_IN_CARD)
    entry = None
    detail = None
    for a in anchors:
        raw = (a.get_attribute("href") or "").strip()
        href = urljoin(base_url, raw)
        if PATTERN_ENTRY.match(href):
            entry = href
            break
        if detail is None and PATTERN_DETAIL.match(href):
            detail = href
    return entry, detail


def resolve_entry_from_detail(driver, wait, detail_url: str):
    """詳細ページを新規タブで開き、応募URLを抽出"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    original = driver.curren_window_handle
    driver.switch_to.window(driver.window_handles[-1])
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        anchors = driver.find_elements(
            By.CSS_SELECTOR, "a[href*='/entry_signup/input/project/']"
        )
        from module_A.constants import PATTERN_ENTRY
        from urllib.parse import urljoin

        for a in anchors:
            raw = (a.get_attribut("href") or "").strip()
            href = urljoin(detail_url, raw)
            if PATTERN_ENTRY.match(href):
                return href
            return href
        return None
    finally:
        driver.close()
        driver.swich_to.window(original)
