"""App changes that make several servers behind the load balancer safe (Feature 6)."""
import importlib

import pytest

from app import create_app
from app.config import TestConfig


def test_footer_names_the_server_and_commit(logged_in, app):
    app.config["NIMBUS_COMMIT"] = "5e5e3060552147eb9c3563cfa18db2d9c7a634b1"
    app.config["NIMBUS_INSTANCE_ID"] = "i-0abc123def4567890"
    page = logged_in.get("/").data
    assert b"i-0abc123def4567890" in page and b"5e5e306" in page


def test_footer_is_quiet_when_not_on_aws(logged_in):
    assert b"Server i-" not in logged_in.get("/").data


def test_mysql_connections_are_capped_per_server(monkeypatch):
    """3 Gunicorn workers x (3 + 2) connections x 3 servers stays well under RDS t3.micro limits."""
    monkeypatch.setenv("DB_HOST", "nimbus.example.internal")
    from app import config
    importlib.reload(config)
    try:
        opts = config.Config.SQLALCHEMY_ENGINE_OPTIONS
        assert opts["pool_size"] == 3 and opts["max_overflow"] == 2
        assert opts["pool_pre_ping"] is True
    finally:
        monkeypatch.delenv("DB_HOST")
        importlib.reload(config)
    assert "pool_size" not in config.Config.SQLALCHEMY_ENGINE_OPTIONS  # SQLite needs no pool settings


def test_archive_runs_only_where_the_lock_is_held(monkeypatch):
    """Every server has the monthly archive timer; only the one holding the lock may run it."""
    from app import archive

    app = create_app(TestConfig)
    calls = []
    monkeypatch.setattr(archive, "_acquire_lock", lambda name: False)
    with app.app_context():
        assert archive.run_exclusively("nimbus-archive", lambda: calls.append(1)) is None
    assert calls == []
    monkeypatch.setattr(archive, "_acquire_lock", lambda name: True)
    monkeypatch.setattr(archive, "_release_lock", lambda name: calls.append("released"))
    with app.app_context():
        assert archive.run_exclusively("nimbus-archive", lambda: 7) == 7
    assert calls == ["released"]


def test_lock_is_a_no_op_on_sqlite():
    from app import archive

    app = create_app(TestConfig)
    with app.app_context():
        assert archive._acquire_lock("nimbus-archive") is True
        archive._release_lock("nimbus-archive")


def test_update_script_is_retired():
    """Deploys are CloudFormation updates of GitCommit (rolling replacement), not git pull on a server."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert not (root / "deploy/update.sh").exists()
    assert "update.sh" not in (root / "README.md").read_text()
