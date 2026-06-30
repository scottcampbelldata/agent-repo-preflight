from agent_repo_preflight.scanner_core.detectors.dependency_risk import (
    BinaryArtifactDetector,
    DependencyRiskDetector,
)
from agent_repo_preflight.scanner_core.filetree import FileEntry, FileTree


def _tree(*pairs, binary=()):
    entries = [FileEntry(p, c, len(c), False) for p, c in pairs]
    for p in binary:
        entries.append(FileEntry(p, None, 1024, True))
    return FileTree("r", entries)


def test_checked_in_binary_by_extension():
    facts = BinaryArtifactDetector().detect(_tree(binary=("vendor/prebuilt.node", "bin/tool.exe")))
    kinds = {f.data["ext"] for f in facts}
    assert facts and facts[0].type == "artifact.checked_in_binary"
    assert ".node" in kinds and ".exe" in kinds


def test_source_files_are_not_binaries():
    facts = BinaryArtifactDetector().detect(_tree(("src/index.js", "x"), ("a.py", "y")))
    assert facts == []


def test_package_json_url_install():
    pkg = '{"dependencies": {"left-pad": "^1.0.0", "evil": "git+https://h/evil.git", "x": "http://h/x.tgz"}}'
    facts = DependencyRiskDetector().detect(_tree(("package.json", pkg)))
    specs = {f.data["name"]: f.data["spec"] for f in facts if f.type == "dep.url_install"}
    assert "evil" in specs and "x" in specs and "left-pad" not in specs


def test_requirements_url_install():
    reqs = "requests==2.31.0\ngit+https://h/pkg.git#egg=pkg\nhttps://h/wheel.whl\n"
    facts = DependencyRiskDetector().detect(_tree(("requirements.txt", reqs)))
    assert sum(1 for f in facts if f.type == "dep.url_install") == 2


def test_npmrc_custom_registry_and_token():
    npmrc = "registry=https://evil.example/npm\n//evil.example/:_authToken=abc\n"
    facts = DependencyRiskDetector().detect(_tree((".npmrc", npmrc)))
    types = {f.type for f in facts}
    assert "dep.custom_registry" in types
