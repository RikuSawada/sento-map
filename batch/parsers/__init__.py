"""都道府県別スクレイパーパーサー。"""
from parsers.base import BaseParser
from parsers.tokyo import TokyoParser
from parsers.kyoto import KyotoParser
from parsers.fukuoka import FukuokaParser
from parsers.kanagawa import KanagawaParser
from parsers.hyogo import HyogoParser

PARSERS: dict[str, type[BaseParser]] = {
    "東京都": TokyoParser,
    "京都府": KyotoParser,
    "福岡県": FukuokaParser,
    "神奈川県": KanagawaParser,
    "兵庫県": HyogoParser,
}

__all__ = [
    "BaseParser", "TokyoParser", "KyotoParser", "FukuokaParser",
    "KanagawaParser", "HyogoParser", "PARSERS",
]
