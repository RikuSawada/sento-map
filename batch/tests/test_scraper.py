"""scraper.run_parser のフォールバック挙動テスト。"""
import logging

from scraper import run_parser
from parsers.base import BaseParser


class DummySaitamaParser(BaseParser):
    prefecture = "埼玉県"
    region = "関東"

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        return []

    def get_list_urls(self) -> list[str]:
        return ["https://saiyoku.jp/"]

    def parse_sento(self, html: str, page_url: str) -> dict:
        return self.make_sento_dict(name="dummy", address="dummy")


def test_run_parser_fallbacks_to_osm_import_on_page1_failure(monkeypatch) -> None:
    parser = DummySaitamaParser()
    logger = logging.getLogger("test")

    monkeypatch.setattr("scraper.fetch", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "scraper.import_new_prefecture",
        lambda session, prefecture, dry_run=False: (5, 2, 10),
    )

    success, skip, fail = run_parser(parser, logger, session=object(), dry_run=False, limit=0)

    assert success == 5
    assert skip == 2
    assert fail == 0


def test_run_parser_dry_run_does_not_fallback_to_osm_import(monkeypatch) -> None:
    parser = DummySaitamaParser()
    logger = logging.getLogger("test")

    monkeypatch.setattr("scraper.fetch", lambda *_args, **_kwargs: None)

    def _unexpected_call(*_args, **_kwargs):
        raise AssertionError("import_new_prefecture should not be called in dry-run")

    monkeypatch.setattr("scraper.import_new_prefecture", _unexpected_call)

    success, skip, fail = run_parser(parser, logger, session=None, dry_run=True, limit=0)

    assert success == 0
    assert skip == 0
    assert fail == 1
