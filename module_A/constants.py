"""サイト構造が変わったときに修正すべき場所を1か所にまとめる」ためのモジュール"""

import re

ROOT = "https://freelance-hub.jp/"

PATTERN_ENTRY = re.compile(
    r"^https://freelance-hub\.jp/entry_signup/input/project/\d+/?$"
)
PATTERN_DETAIL = re.compile(r"^https://freelance-hub\.jp/project/\d+/?$")
# \d+ は「数字1文字以上」という意味
# /?$ は「最後の / があってもなくてもOK」

SEL_CARD = ".ProjectCard"
SEL_TITLE = "h3.ProjectCard_Title"
SEL_ANCHORS_IN_CARD = (
    "a.ProjectDetail_Cta, "
    "h3.ProjectCard_Title a, "
    "a[href*='/entry_signup/input/project/'], "
    "a[href^='/project/']"
)

""""
パターン                             意味
^                                   文字列の先頭にマッチ
https://freelance-hub\.jp/          固定のURLドメイン（ドットは \. でエスケープ）
entry_signup/input/project/         応募ページの固定パス
\d+                                 数字が1文字以上（=プロジェクトID部分）
/?                                  末尾の / があってもなくてもOK
$                                   文字列の終端にマッチ

"""
