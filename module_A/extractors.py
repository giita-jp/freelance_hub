"""カード要素／詳細ページから応募リンクを抽出するユーティリティ。

本モジュールは次の2つの関数を提供します：
- find_entry_in_card(card, base_url): 1枚の案件カードから応募URL（なければ詳細URL）を抽出
- resolve_entry_from_detail(driver, wait, detail_url): 詳細ページを開いて応募URLを抽出
"""

from typing import Optional, Tuple
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from module_A.constants import PATTERN_ENTRY, PATTERN_DETAIL, SEL_ANCHORS_IN_CARD


def find_entry_in_card(card, base_url: str) -> Tuple[Optional[str], Optional[str]]:
    """案件カード（1枚）から応募URLまたは詳細URLを抽出する。

    まずカード内のリンク群（`SEL_ANCHORS_IN_CARD` に一致）を走査し、
    応募URL（ENTRY）が見つかればそれを返す。見つからない場合に限り、
    代替として詳細URL（DETAIL）を拾っておき、タプルの第2要素として返す。

    返値の構成:
        (entry_url, detail_url)
        - entry_url: 応募URLが見つかった場合にそのURL、見つからなければ None
        - detail_url: 応募URLが見つからず、かつ詳細URLが見つかった場合にそのURL、なければ None

    Args:
        card (WebElement): `.ProjectCard` に相当するカードのルート要素。
        base_url (str): 相対URLを絶対化するための基準URL（例: 一覧ページのURL）。

    Returns:
        Tuple[Optional[str], Optional[str]]: (entry_url, detail_url)

    Notes:
        - href が相対パスの場合に備え、常に `urljoin(base_url, raw_href)` で正規化します。
        - 「ENTRY」と「DETAIL」は正規表現 `PATTERN_ENTRY`, `PATTERN_DETAIL` で判定します。
    """
    # anchors = その案件カード (card) の中にあるすべての <a> タグ（リンク要素）を集めたリスト
    anchors = card.find_elements(By.CSS_SELECTOR, SEL_ANCHORS_IN_CARD)
    entry = None
    # detail = 案件の“詳細ページ”のURLを一時的に保持しておく変数
    detail = None
    for a in anchors:
        # strip() は、スペースやタブ、改行の削除をしている
        raw = (a.get_attribute("href") or "").strip()
        href = urljoin(base_url, raw)

        # 応募URLが見つかったら最優先で返すため entry を確定して break
        if PATTERN_ENTRY.match(href):
            entry = href
            break

        # 応募URLが未発見の間に、最初に見つかった詳細URLを控えておく
        if detail is None and PATTERN_DETAIL.match(href):
            detail = href
    return entry, detail


def resolve_entry_from_detail(driver, wait, detail_url: str) -> Optional[str]:
    """詳細ページを新規タブで開き、応募URL（ENTRY）を抽出して返す。

    手順:
        1) `window.open(detail_url)` で新規タブを開き、そのタブにフォーカスを移す
        2) body の出現まで軽く待機
        3) 応募URLパターンに合致する a[href*="/entry_signup/input/project/"] を走査
        4) 見つかった時点で絶対URLに正規化して返す
        5) 見つからなければ None を返す
        6) 最後に新規タブを閉じ、元のタブへ戻す（必ず実行）

    Args:
        driver (WebDriver): Selenium WebDriver。
        wait (WebDriverWait): 待機用の WebDriverWait。
        detail_url (str): 参照する詳細ページの絶対URL。

    Returns:
        Optional[str]: 応募URLが見つかればその絶対URL、見つからなければ None。

    Raises:
        Exception: タブ操作やDOM取得で Selenium 側の例外が発生する可能性があります。
                ただしタブのクリーンアップは finally 節で必ず実行します。

    Notes:
        - 新規タブで開く理由は、一覧ページの状態を保ったまま詳細ページを確認するためです。
        - href が相対パスの場合に備え、常に `urljoin(detail_url, raw_href)` で絶対化します。
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    original = driver.current_window_handle

    # 新規タブを開いてフォーカスを移動
    driver.execute_script("window.open(arguments[0]);", detail_url)
    driver.switch_to.window(driver.window_handles[-1])
    try:
        # ページが描画される最低限の待機
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        # 応募リンク候補を走査
        anchors = driver.find_elements(
            By.CSS_SELECTOR, "a[href*='/entry_signup/input/project/']"
        )
        for a in anchors:
            raw = (a.get_attribute("href") or "").strip()
            href = urljoin(detail_url, raw)
            if PATTERN_ENTRY.match(href):
                return href

        # 見つからなければ None
        return None
    finally:
        # 新規タブを確実に閉じ、元のタブへ戻す
        driver.close()
        driver.switch_to.window(original)
