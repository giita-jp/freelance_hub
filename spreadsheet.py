import os
from dotenv import load_dotenv
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials  # ← google-auth を使用


class GoogleSheetClient:
    def __init__(self, credentials_path: str, sheet_id: str):
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = self._authorize()
        self.sheet = self.client.open_by_key(sheet_id).sheet1

    def _authorize(self):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(
            self.credentials_path, scopes=scopes
        )
        return gspread.authorize(creds)

    def get_dataframe(self):
        """シート全体をDataFrameで取得"""
        data = self.sheet.get_all_values()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])


def main():
    load_dotenv()  # ここだけで .env を読む（副作用を閉じ込める）
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not credentials_path:
        raise RuntimeError("環境変数 GOOGLE_CREDENTIALS_PATH が未設定です。")
    if not sheet_id:
        raise RuntimeError("環境変数 GOOGLE_SHEET_ID が未設定です。")

    client = GoogleSheetClient(credentials_path, sheet_id)
    df = client.get_dataframe()
    print(df.head(10))


if __name__ == "__main__":
    main()
