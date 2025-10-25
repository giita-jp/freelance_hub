import logging


RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[90m",  # 薄い灰色（Bright Black / Gray）
    logging.INFO: "\033[34m",  # 青
    logging.WARNING: "\033[33m",  # 黄
    logging.ERROR: "\033[31m",  # 赤
    logging.CRITICAL: "\033[35m",  # 濃いピンク（Magenta）
}


class ColorOnlyFormatter(logging.Formatter):
    def format(
        self, record
    ):  # record とは、Python の logging がログ出力時に自動で作って渡してくるオブジェク
        # まず通常のフォーマット処理を済ませる（% 展開や例外文字列の付与など）
        s = super().format(record)
        # その結果全体にだけ色をかける（record.msg/levelname は一切いじらない）
        color = COLORS.get(record.levelno, RESET)
        return f"{color}{s}{RESET}"


def get_logger(name="myapp"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        # ★ここで色付きフォーマッタを設定
        handler.setFormatter(
            ColorOnlyFormatter("%(asctime)s %(levelname)s : %(message)s")
        )
        logger.addHandler(handler)
        logger.propagate = False
    return logger


# 動作テスト
def main():
    log = get_logger()
    log.debug("これはデバッグメッセージ（薄い灰色）")
    log.info("これは情報メッセージ（青）")
    log.warning("これは警告です（黄）")
    log.error("これはエラーです（赤）")
    log.critical("これは致命的なエラーです（濃いピンク）")


if __name__ == "__main__":
    main()
