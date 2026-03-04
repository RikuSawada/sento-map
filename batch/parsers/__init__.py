"""都道府県別スクレイパーパーサー。"""
from parsers.base import BaseParser
from parsers.tokyo import TokyoParser
from parsers.kyoto import KyotoParser
from parsers.fukuoka import FukuokaParser
from parsers.saitama import SaitamaParser
from parsers.chiba import ChibaParser
from parsers.hokkaido import HokkaidoParser

PARSERS: dict[str, type[BaseParser]] = {
    "東京都": TokyoParser,
    "京都府": KyotoParser,
    "福岡県": FukuokaParser,
    "埼玉県": SaitamaParser,
    "千葉県": ChibaParser,
    "北海道": HokkaidoParser,
}

__all__ = [
    "BaseParser", "TokyoParser", "KyotoParser", "FukuokaParser",
    "SaitamaParser", "ChibaParser", "HokkaidoParser", "PARSERS",
]
