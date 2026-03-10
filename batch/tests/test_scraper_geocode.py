"""scraper の後処理（座標補完）テスト。"""
import logging

from scraper import _post_geocode_if_needed


def test_post_geocode_runs_only_for_hokkaido(monkeypatch) -> None:
    logger = logging.getLogger("test")
    called = {}

    def _fake_geocode(session, prefecture, dry_run=False):
        called["session"] = session
        called["prefecture"] = prefecture
        called["dry_run"] = dry_run
        return (3, 1, 4)

    monkeypatch.setattr("scraper.geocode_prefecture", _fake_geocode)

    _post_geocode_if_needed("北海道", logger, session=object(), dry_run=False)

    assert called["prefecture"] == "北海道"
    assert called["dry_run"] is False


def test_post_geocode_skips_on_dry_run_or_non_hokkaido(monkeypatch) -> None:
    logger = logging.getLogger("test")

    def _unexpected_call(*_args, **_kwargs):
        raise AssertionError("geocode_prefecture should not be called")

    monkeypatch.setattr("scraper.geocode_prefecture", _unexpected_call)

    _post_geocode_if_needed("北海道", logger, session=object(), dry_run=True)
    _post_geocode_if_needed("東京都", logger, session=object(), dry_run=False)


def test_post_geocode_skips_when_session_is_none(monkeypatch) -> None:
    logger = logging.getLogger("test")

    def _unexpected_call(*_args, **_kwargs):
        raise AssertionError("geocode_prefecture should not be called when session is None")

    monkeypatch.setattr("scraper.geocode_prefecture", _unexpected_call)

    _post_geocode_if_needed("北海道", logger, session=None, dry_run=False)
