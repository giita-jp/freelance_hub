from logger import get_logger
from module_A.scraper import FreelanceHubScraper


def main():
    logger = get_logger()
    start_url = "https://freelance-hub.jp/project/skill/7/"
    try:
        with FreelanceHubScraper(base_url=start_url, logger=logger) as scraper:
            scraper.open()
            projects = scraper.collect_all_projects(max_pages=5)  # Noneで全ページ
            logger.debug("出力開始")
            for p in projects:
                print(p)
            logger.debug("出力完了")
    except Exception as e:
        logger.error(f"main内エラー: {e}")
        raise


if __name__ == "__main__":
    main()
