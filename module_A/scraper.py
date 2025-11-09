"""このモジュールは、某サイトから案件一覧をページを跨いで収集するための司令塔モジュール"""

from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from logger import get_logger
from module_A.constants import SEL_CARD, SEL_TITLE
from module_A.scrolling import scroll_to_load, wait_cards
from module_A.extractors import find_entry_in_card, resolve_entry_from_detail
from module_A.pagination import goto_next_page


class FreelanceHubScraper:
    """Freelance Hub の案件一覧を巡回し、タイトルと応募 URL を収集するスクレイパー。

    本クラスは以下の責務を持ちます：
        - 指定 URL のページを開く（`open`）
        - 遅延読み込み（Lazy Load）対策でスクロールする（`scroll_to_load` の利用）
        - カード単位で案件のタイトルとリンクを抽出する（`collect_projects`）
        - 「次へ」ボタンや `?page=N` によるページネーションを自動で辿る（`collect_all_projects`）

    依存モジュール（module_A.*）に対しては「単一責務の原則」を満たすように分割済み。
    """

    def __init__(
        self,
        base_url: str,
        driver: Optional[WebDriver] = None,
        wait_time: int = 15,
        logger=None,
    ):
        """スクレイパーを初期化する。

        Args:
            base_url (str): 収集を開始する一覧ページの URL。
            driver (Optional[WebDriver], optional): 既存の Selenium WebDriver。
                指定がない場合は `webdriver.Chrome()` を自動生成する。
            wait_time (int, optional): WebDriverWait の既定タイムアウト秒。デフォルト 15 秒。
            logger (optional): ロガー。指定がない場合は `get_logger()` を使用。

        Note:
            `driver` を外部から注入できるため、テストや既存セッションの再利用が容易。
        """
        self.base_url = base_url
        self.driver = driver or webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, wait_time)
        self.logger = logger or get_logger()

    def __enter__(self):
        """with 構文で利用するためのエントリポイント。

        Returns:
            FreelanceHubScraper: 自身のインスタンス。
        """
        return self

    def __exit__(self, exc_type, exc, tb):
        """with ブロックを抜ける際に呼ばれるクリーンアップ処理。

        可能な限り `driver.quit()` を確実に実行する。
        例外を握りつぶさないため、常に False を返す（伝播させる）。

        Args:
            exc_type: 例外タイプ
            exc: 例外インスタンス
            tb: トレースバック

        Returns:
            bool: False（例外は外に伝播）
        """
        try:
            self.driver.quit()
        finally:
            return False

    # 公開API
    def open(self):
        """`base_url` のページを開く。

        Raises:
            Exception: ドライバの起動やネットワーク障害等により遷移できない場合。
        """
        self.logger.debug("ページオープン開始")
        self.driver.get(self.base_url)
        self.logger.debug("ページオープン完了")

    def collect_projects(self) -> List[Dict[str, Optional[str]]]:
        """現在のページから案件カードを走査し、(タイトル, 応募URL) を収集する。

        動作概要:
            1) カード要素の出現を待機（`wait_cards`）
            2) 各カードからタイトルを抽出
            3) `find_entry_in_card` で応募 URL を優先的に探索し、
                見つからなければ詳細 URL を保持
            4) 応募 URL が未取得で詳細 URL がある場合は、
                `resolve_entry_from_detail` で詳細ページから応募 URL を補完

        Returns:
            List[Dict[str, Optional[str]]]:
                各要素は `{"title": str, "link": Optional[str]}` 形式の辞書。
                `link` は取得できなければ `None`。
        """
        # wait_cards() → 「カードが全て表示されるまで待機」
        # SEL_CARD → 定数で指定された .ProjectCard 要素を取得
        wait_cards(self.wait, SEL_CARD, logger=self.logger)
        cards = self.driver.find_elements(By.CSS_SELECTOR, SEL_CARD)
        self.logger.debug(f"cards={len(cards)}")

        projects: List[Dict[str, Optional[str]]] = []
        for idx, card in enumerate(cards):
            try:
                title = card.find_element(By.CSS_SELECTOR, SEL_TITLE).text.strip()
            except Exception:
                self.logger.debug(f"[{idx}] タイトル未検出につきスキップ")
                continue

            entry_url, detail_url = find_entry_in_card(card, self.base_url)
            if not entry_url and detail_url:
                try:
                    entry_url = resolve_entry_from_detail(
                        self.driver, self.wait, detail_url
                    )
                except Exception as e:
                    self.logger.debug(f"[{idx}] 詳細ページ補完失敗: {e}")
                    entry_url = None

            projects.append({"title": title, "link": entry_url})

        self.logger.debug(f"取得プロジェクト数={len(projects)}")
        return projects

    def collect_all_projects(
        self, max_pages: int | None = None
    ) -> List[Dict[str, Optional[str]]]:
        """ページネーションを自動で辿り、複数ページにわたって案件を収集する。

        処理の流れ:
            各ページで
                - 遅延読み込み対策スクロール（`scroll_to_load`）
                - `collect_projects` により (title, link) の配列を取得
                - 既出 (title, link) の重複は `seen` セットで排除
            を行い、`goto_next_page` で次ページへ遷移。
            `max_pages` 指定があれば、そのページ数で収集を打ち切る。

        Args:
            max_pages (int | None, optional): 収集する最大ページ数。
                None の場合は「次へ」が無くなるまで巡回。

        Returns:
            List[Dict[str, Optional[str]]]:
                すべてのページから集約した案件リスト。
                各要素は `{"title": str, "link": Optional[str]}`。
        """
        all_projects, seen = [], set()
        page_count = 0
        while True:
            page_count += 1
            scroll_to_load(self.driver, logger=self.logger)
            projects = self.collect_projects()
            for p in projects:
                key = (p.get("title", ""), p.get("link", ""))
                if key not in seen:
                    seen.add(key)
                    all_projects.append(p)
            if max_pages and page_count >= max_pages:
                self.logger.debug(f"max_pages={max_pages} 到達、停止")
                break
            if not goto_next_page(self.driver, self.wait, logger=self.logger):
                break
        self.logger.debug(f"総取得件数={len(all_projects)} / 総ページ={page_count}")
        return all_projects
