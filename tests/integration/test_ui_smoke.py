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


def test_bot_match_rejects_invalid_hand_count(client):
    resp = client.post("/api/bot-vs-bot/start", json={"hands": "not-a-number"})
    assert resp.status_code == 400


def test_bot_match_reports_progress_hand_by_hand(client):
    pytest.importorskip("poker_ai.poker_engine")
    resp = client.post(
        "/api/bot-vs-bot/start", json={"botA": "v0", "botB": "v1", "hands": 30}
    )
    assert resp.status_code == 200

    seen = []
    while True:
        data = client.get("/api/bot-vs-bot/next").get_json()
        seen.append(data)
        assert data["p0_wins"] + data["p1_wins"] <= data["hand"]
        assert data["p0_stack"] + data["p1_stack"] == 2000
        if data["finished"]:
            break

    assert [d["hand"] for d in seen] == sorted(d["hand"] for d in seen)
    assert seen[-1]["hand"] == seen[-1]["total_hands"]
