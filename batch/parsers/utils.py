"""パーサー共通ユーティリティ。"""
from typing import Optional

from bs4 import BeautifulSoup


def extract_label_value(soup: BeautifulSoup, label: str) -> Optional[str]:
    """dt または th テキストが label に一致する dd/td の値を返す。"""
    for dt in soup.find_all(["dt", "th"]):
        if label in dt.get_text(strip=True):
            sibling = dt.find_next_sibling(["dd", "td"])
            if sibling:
                val = sibling.get_text(strip=True)
                if val:
                    return val
    return None
