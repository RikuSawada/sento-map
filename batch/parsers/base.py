"""スクレイパーパーサーの共通インターフェース。"""
from abc import ABC, abstractmethod
from typing import Optional

from bs4 import BeautifulSoup


class BaseParser(ABC):
    """都道府県銭湯組合サイトの共通パーサーインターフェース。

    各都道府県のパーサーはこのクラスを継承して実装する。
    """

    #: 対象都道府県名（例: '東京都', '大阪府'）
    prefecture: str
    #: 地域区分（例: '関東', '関西'）
    region: str

    @abstractmethod
    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        """一覧ページ HTML から個別ページ URL リストを抽出する。

        Args:
            html: 一覧ページの HTML
            page_url: 取得元 URL（ログ用）

        Returns:
            個別ページ URL のリスト
        """
        ...

    @abstractmethod
    def get_list_urls(self) -> list[str]:
        """スクレイピング対象の一覧ページ URL リストを返す。

        ページネーションが必要なサイトは fetch 済みの最初のページ HTML から
        算出するため、引数として HTML を受け取る形にする場合は
        サブクラスでオーバーライドすること。

        Returns:
            一覧ページ URL のリスト（ページ1から順）
        """
        ...

    @abstractmethod
    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        """個別ページ HTML から銭湯データを抽出する。

        Args:
            html: 個別ページの HTML
            page_url: 取得元 URL（`source_url` として保存）

        Returns:
            dict: {name, address, lat?, lng?, phone?, url?, open_hours?, holiday?,
                   prefecture, region, source_url, facility_type?}
            None: 必須フィールド（name, address）が取得できなかった場合
        """
        ...

    @staticmethod
    def extract_label_value(soup: BeautifulSoup, label: str) -> Optional[str]:
        """dt/th テキストが label に一致する dd/td の値を返す。

        strong/b タグに label がある場合も対応する。
        """
        for dt in soup.find_all(["dt", "th"]):
            if label in dt.get_text(strip=True):
                sibling = dt.find_next_sibling(["dd", "td"])
                if sibling:
                    val = sibling.get_text(strip=True)
                    if val:
                        return val
        for strong in soup.find_all(["strong", "b"]):
            if label in strong.get_text(strip=True):
                parent = strong.parent
                if parent:
                    text = parent.get_text(strip=True).replace(label, "").strip()
                    if text and len(text) < 100:
                        return text
        return None

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """全一覧ページ URL を返す。ページネーションが動的なサイトはオーバーライドする。"""
        return self.get_list_urls()

    def make_sento_dict(
        self,
        name: str,
        address: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        phone: Optional[str] = None,
        url: Optional[str] = None,
        open_hours: Optional[str] = None,
        holiday: Optional[str] = None,
        source_url: Optional[str] = None,
        facility_type: Optional[str] = None,
    ) -> dict:
        """共通フィールドを含む銭湯データ dict を生成する。"""
        return {
            "name": name,
            "address": address,
            "lat": lat,
            "lng": lng,
            "phone": phone,
            "url": url,
            "open_hours": open_hours,
            "holiday": holiday,
            "prefecture": self.prefecture,
            "region": self.region,
            "source_url": source_url,
            "facility_type": facility_type,
        }
