import os
from dotenv import load_dotenv
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials  # ← google-auth を使用
from logger import get_logger


class GoogleSheetClient:
    def __init__(self, credentials_path: str, sheet_id: str, logger):
        self.logger = logger
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = self._authorize()
        self.sheet = self.client.open_by_key(sheet_id).sheet1

    def _authorize(self):
        try:
            self.logger.debug(f"ログイン認証処理、開始")
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
            self.logger.debug(f"ログイン認証処理、完了")
            return gspread.authorize(creds)
        except Exception as e:
            self.logger.error(f"ログイン認証処理、失敗: \n{e}")
            raise

    def get_titles(self):
        try:
            self.logger.debug(f"スプシタイトル、リスト化、開始")
            """シート全体をDataFrameで取得"""
            data = self.sheet.get_all_values()
            if not data:
                self.logger.warning("スプシが空です。空のリストを返します。")
                return []
            self.logger.debug(f"スプシタイトル、リスト化、開始")
            return data[0]  # ← タイトル行（1行目）をリストで返す
            # return pd.DataFrame(data[1:], columns=data[0])
        except Exception as e:
            self.logger.error(f"プシタイトル、リスト化、失敗: \n{e}")
            raise


def main():
    logger = get_logger()
    load_dotenv()  # ここだけで .env を読む（副作用を閉じ込める）
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not credentials_path:
        raise RuntimeError("環境変数 GOOGLE_CREDENTIALS_PATH が未設定です。")
    if not sheet_id:
        raise RuntimeError("環境変数 GOOGLE_SHEET_ID が未設定です。")

    client = GoogleSheetClient(credentials_path, sheet_id, logger)
    df = client.get_titles()
    print(df)
    print(type(df))


if __name__ == "__main__":
    main()
