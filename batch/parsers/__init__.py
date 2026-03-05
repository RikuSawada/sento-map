"""都道府県別スクレイパーパーサー。"""
from parsers.base import BaseParser
from parsers.tokyo import TokyoParser
from parsers.kyoto import KyotoParser
from parsers.fukuoka import FukuokaParser
from parsers.osaka import OsakaParser
from parsers.aichi import AichiParser

PARSERS: dict[str, type[BaseParser]] = {
    "東京都": TokyoParser,
    "京都府": KyotoParser,
    "福岡県": FukuokaParser,
    "大阪府": OsakaParser,
    "愛知県": AichiParser,
}

__all__ = [
    "BaseParser", "TokyoParser", "KyotoParser", "FukuokaParser",
    "OsakaParser", "AichiParser", "PARSERS",
]
