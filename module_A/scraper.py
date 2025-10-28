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
    def __init__(
        self,
        base_url: str,
        driver: Optional[WebDriver] = None,
        wait_time: int = 15,
        logger=None,
    ):
        self.base_url = base_url
        self.driver = driver or webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, wait_time)
        self.logger = logger or get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.driver.quit()
        finally:
            return False

    # 公開API
    def open(self):
        # この関数の目的：指定URLを開く
        self.logger.debug("ページオープン開始")
        self.driver.get(self.base_url)
        self.logger.debug("ページオープン完了")

    def collect_projects(self) -> List[Dict[str, Optional[str]]]:
        # この関数の目的：指定URLを開く
        wait_cards(self.wait, SEL_CARD, logger=self.logger)
        # wait_cards() → 「カードが全て表示されるまで待機」
        # SEL_CARD → 定数で指定された .ProjectCard 要素を取得
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
        # この関数の目的：ページネーションを自動でたどって全ページ分の案件を収集する
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
