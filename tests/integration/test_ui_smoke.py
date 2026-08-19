"""Basic Flask UI smoke tests (no engine required for index routes)."""

from __future__ import annotations

import pytest


@pytest.fixture
def client():
    pytest.importorskip("flask")
    import importlib.util
    from pathlib import Path

    app_path = Path("ui/app.py")
    spec = importlib.util.spec_from_file_location("ui_app", app_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.config["TESTING"] = True
    return module.app.test_client()


def test_index_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_play_page_loads(client):
    resp = client.get("/play")
    assert resp.status_code == 200
