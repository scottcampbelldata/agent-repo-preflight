from agent_repo_preflight.web.store import SqliteScanStore


def _report():
    return {
        "repo": {"source": "https://github.com/o/r", "name": "r"},
        "verdict": "FAIL",
        "score": 28,
        "findings": [],
        "schema_version": "1.0",
    }


def test_save_get_roundtrip(tmp_path):
    store = SqliteScanStore(str(tmp_path / "s.db"))
    sid = store.save(_report(), created_at="2026-06-29T00:00:00Z")
    assert isinstance(sid, str) and sid
    got = store.get(sid)
    assert got["verdict"] == "FAIL" and got["repo"]["name"] == "r"


def test_get_missing_returns_none(tmp_path):
    store = SqliteScanStore(str(tmp_path / "s.db"))
    assert store.get("nope") is None


def test_list_recent_orders_newest_first(tmp_path):
    store = SqliteScanStore(str(tmp_path / "s.db"))
    a = store.save(_report(), created_at="2026-06-29T00:00:00Z")
    b = store.save(_report(), created_at="2026-06-29T01:00:00Z")
    rows = store.list_recent()
    assert [r["id"] for r in rows][:2] == [b, a]
    assert "verdict" in rows[0] and "report_json" not in rows[0]
