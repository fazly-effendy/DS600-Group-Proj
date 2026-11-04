"""A saved 'price at the time of discussion' must never be made-up demo data.

These tests cover the fix for a defect found in the 1 Nov 2026 audit: when Yahoo
failed and DEMO_FALLBACK was on, a synthetic price could be saved into a client
record and shown as if it were real.
"""
from pathlib import Path

import pytest
import sqlalchemy as sa

from app import create_app
from app.config import TestConfig
from app.market import DemoProvider, MarketDataError
from app.models import Snapshot, User, db

ROOT = Path(__file__).resolve().parents[1]


class FakeYahoo:
    """Stands in for YahooProvider. `fail=True` simulates a rate limit."""

    name = "yahoo"

    def __init__(self, fail=False):
        self.fail = fail
        self.demo = DemoProvider()

    def _check(self):
        if self.fail:
            raise MarketDataError("simulated Yahoo rate limit")

    def info(self, ticker):
        self._check()
        return {**self.demo.info(ticker), "name": f"{ticker} Live Corp"}

    def history(self, ticker, period):
        self._check()
        return [("2026-10-30", 101.0), ("2026-10-31", 123.45)]

    def fundamentals(self, ticker):
        self._check()
        return self.demo.fundamentals(ticker)


def make_app(provider="yahoo", fallback=True, yahoo_fails=False, uri="sqlite:///:memory:"):
    cfg = type("Cfg", (TestConfig,), {
        "MARKET_DATA_PROVIDER": provider,
        "DEMO_FALLBACK": fallback,
        "SQLALCHEMY_DATABASE_URI": uri,
    })
    app = create_app(cfg)
    market = app.extensions["market"]
    if provider == "yahoo":
        market.primary = FakeYahoo(fail=yahoo_fails)
    with app.app_context():
        user = User(username="rm1", full_name="Test RM")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    client = app.test_client()
    client.post("/login", data={"username": "rm1", "password": "password123"})
    return app, client


NEW_CLIENT = {"client_id": "__new__", "new_client_code": "C-9001", "new_client_name": "Fictional Client"}


def test_demo_fallback_price_is_never_saved():
    app, client = make_app(fallback=True, yahoo_fails=True)
    r = client.post("/snapshots/new", data={**NEW_CLIENT, "ticker": "AAPL", "price": ""})
    assert r.status_code == 200
    assert b"live price" in r.data.lower()
    with app.app_context():
        assert Snapshot.query.count() == 0


def test_live_price_is_saved_with_its_source():
    app, client = make_app(fallback=True, yahoo_fails=False)
    client.post("/snapshots/new", data={**NEW_CLIENT, "ticker": "AAPL", "price": ""})
    with app.app_context():
        s = Snapshot.query.one()
        assert float(s.price_at_discussion) == 123.45
        assert s.price_source == "yahoo"


def test_typed_price_is_recorded_as_entered_by_rm():
    app, client = make_app(fallback=True, yahoo_fails=True)
    client.post("/snapshots/new", data={**NEW_CLIENT, "ticker": "AAPL", "price": "150.25"})
    with app.app_context():
        s = Snapshot.query.one()
        assert float(s.price_at_discussion) == 150.25
        assert s.price_source == "manual"
    page = client.get(f"/clients/{s.client_id}")
    assert b"Entered by RM" in page.data


def test_explicit_demo_mode_saves_and_labels_demo_prices():
    app, client = make_app(provider="demo")
    client.post("/snapshots/new", data={**NEW_CLIENT, "ticker": "AAPL", "price": ""})
    with app.app_context():
        s = Snapshot.query.one()
        assert s.price_source == "demo"
    assert b"Demo data" in client.get(f"/clients/{s.client_id}").data
    assert b"Demo data" in client.get("/snapshots").data
    assert "demo" in client.get("/snapshots/export.csv").data.decode()


def test_save_link_does_not_carry_a_price():
    """The compare page's Save link used to put the (possibly demo) price in the URL."""
    _, client = make_app(provider="demo")
    page = client.get("/snapshots/new?ticker=AAPL&price=999.99")
    assert b"999.99" not in page.data
    js = (ROOT / "app/static/js/compare.js").read_text()
    assert "&price=" not in js


def test_editing_notes_keeps_the_original_price_source():
    app, client = make_app(fallback=False, yahoo_fails=False)
    client.post("/snapshots/new", data={**NEW_CLIENT, "ticker": "AAPL", "price": ""})
    with app.app_context():
        s = Snapshot.query.one()
        sid, cid = s.id, s.client_id
    client.post(f"/snapshots/{sid}/edit", data={"client_id": str(cid), "ticker": "AAPL",
                                               "price": "123.4500", "notes": "updated"})
    with app.app_context():
        s = db.session.get(Snapshot, sid)
        assert s.notes == "updated" and s.price_source == "yahoo"


def test_demo_fallback_is_off_by_default_and_on_aws(monkeypatch):
    monkeypatch.delenv("DEMO_FALLBACK", raising=False)
    from app import config
    assert config.DEMO_FALLBACK_DEFAULT is False
    assert config._bool("DEMO_FALLBACK", config.DEMO_FALLBACK_DEFAULT) is False
    template = (ROOT / "infra/nimbus-merged-stack.yaml").read_text()
    assert "DEMO_FALLBACK=false" in template and "DEMO_FALLBACK=true" not in template
    assert "DEMO_FALLBACK=false" in (ROOT / ".env.example").read_text()


def test_existing_database_gets_the_new_column(tmp_path):
    """RDS tables created before this change have no price_source column."""
    uri = f"sqlite:///{tmp_path / 'old.db'}"
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(64) NOT NULL UNIQUE, "
                             "full_name VARCHAR(120) NOT NULL, password_hash VARCHAR(255) NOT NULL, created_at DATETIME NOT NULL)"))
        conn.execute(sa.text("CREATE TABLE clients (id INTEGER PRIMARY KEY, rm_id INTEGER NOT NULL, client_code VARCHAR(32) NOT NULL, "
                             "name VARCHAR(120) NOT NULL, segment VARCHAR(40), risk_profile VARCHAR(20), created_at DATETIME NOT NULL)"))
        conn.execute(sa.text("CREATE TABLE snapshots (id INTEGER PRIMARY KEY, rm_id INTEGER NOT NULL, client_id INTEGER NOT NULL, "
                             "ticker VARCHAR(16) NOT NULL, company_name VARCHAR(160), price_at_discussion NUMERIC(14,4) NOT NULL, "
                             "currency VARCHAR(8), discussed_on DATE NOT NULL, interest_level VARCHAR(10), tags VARCHAR(255), "
                             "notes TEXT, follow_up_on DATE, created_at DATETIME NOT NULL)"))
    engine.dispose()
    app, client = make_app(provider="demo", uri=uri)
    with app.app_context():
        cols = {c["name"] for c in sa.inspect(db.engine).get_columns("snapshots")}
    assert "price_source" in cols
    assert client.get("/snapshots").status_code == 200
