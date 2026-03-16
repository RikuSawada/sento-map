"""都道府県別スクレイパーパーサー。"""
from parsers.base import BaseParser
from parsers.tokyo import TokyoParser
from parsers.kyoto import KyotoParser
from parsers.fukuoka import FukuokaParser
from parsers.osaka import OsakaParser
from parsers.aichi import AichiParser
from parsers.kanagawa import KanagawaParser
from parsers.hyogo import HyogoParser
from parsers.saitama import SaitamaParser
from parsers.chiba import ChibaParser
from parsers.hokkaido import HokkaidoParser
from parsers.kochi import KochiParser

PARSERS: dict[str, type[BaseParser]] = {
    "東京都": TokyoParser,
    "京都府": KyotoParser,
    "福岡県": FukuokaParser,
    "大阪府": OsakaParser,
    "愛知県": AichiParser,
    "神奈川県": KanagawaParser,
    "兵庫県": HyogoParser,
    "埼玉県": SaitamaParser,
    "千葉県": ChibaParser,
    "北海道": HokkaidoParser,
    "高知県": KochiParser,
}

__all__ = [
    "BaseParser", "TokyoParser", "KyotoParser", "FukuokaParser",
    "OsakaParser", "AichiParser", "KanagawaParser", "HyogoParser",
    "SaitamaParser", "ChibaParser", "HokkaidoParser", "KochiParser", "PARSERS",
]
