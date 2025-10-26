from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from logger import get_logger
import time


class ChromeManager:
    def __init__(self, logger):
        self.logger = logger

    def get_chrome_options(self, *args: str):
        try:
            self.logger.debug(f"オプション付加、開始")
            options = Options()
            for arg in args:
                options.add_argument(arg)
            self.logger.debug(f"オプション付加、完了")
            return options
        except Exception as e:
            self.logger.error(f"オプション付加、失敗: \n{e}")
            raise

    def start_chrome(self, options: Options | None = None) -> WebDriver:
        try:
            self.logger.debug(f"chrome立ち上げ、開始")
            driver = webdriver.Chrome(options)
            self.logger.debug(f"chrome立ち上げ、完了")
            return driver
        except Exception as e:
            self.logger.error(f"chrome立ち上げ、失敗: \n{e}")
            raise

    def open_site(self, driver: WebDriver, url: str) -> WebDriver:
        try:
            self.logger.debug(f"url取得、開始")
            driver.get(url)
            self.logger.debug(f"url取得、終了")
            return driver
        except Exception as e:
            self.logger.error(f"url取得、失敗: \n{e}")
            raise


def main():
    logger = get_logger()
    url = "https://freelance-hub.jp/project/skill/7/"
    chrome_manager = ChromeManager(logger)
    try:
        logger.debug(f"main関数、開始")
        options = chrome_manager.get_chrome_options("--incognito")
        driver = chrome_manager.start_chrome(options)
        chrome_manager.open_site(driver, url)
        time.sleep(10)
        logger.debug(f"main関数、完了")
    except Exception as e:
        logger.debug(f"main関数、失敗: \n{e}")


if __name__ == "__main__":
    main()
