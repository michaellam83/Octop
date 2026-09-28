"""Tests for user-scoped ZDX credential storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from octop.infra.agents.zdx_credentials import ZdxCredentialStore
from octop.infra.db.migrate import run_migrations
from octop.infra.db.pool import SqlitePool
from octop.infra.db.repos.secrets import SecretRepo


def test_zdx_credentials_are_encrypted_and_isolated(tmp_path: Path) -> None:
    db = SqlitePool(tmp_path / "octop.db")
    run_migrations(db)
    secrets = SecretRepo(db)
    store = ZdxCredentialStore(secrets)

    store.save(11, api_key="sk-user-a", userid="oa.a")
    store.save(12, api_key="sk-user-b", userid="oa.b")

    assert store.get(11).userid == "oa.a"
    assert store.get(12).api_key == "sk-user-b"
    assert b"sk-user-a" not in (secrets.get("zdx.credentials.11") or b"")
    assert secrets.get("zdx.credentials.11") != secrets.get("zdx.credentials.12")

    store.delete(11)
    assert store.get(11) is None
    assert store.get(12).userid == "oa.b"


def test_zdx_credentials_reject_control_characters(tmp_path: Path) -> None:
    db = SqlitePool(tmp_path / "octop.db")
    run_migrations(db)
    store = ZdxCredentialStore(SecretRepo(db))

    with pytest.raises(ValueError):
        store.save(11, api_key="sk-user\n-a", userid="oa.a")
