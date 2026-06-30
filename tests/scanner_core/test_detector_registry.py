from agent_repo_preflight.scanner_core.facts import Fact
from agent_repo_preflight.scanner_core.detectors.base import run_detectors
from agent_repo_preflight.scanner_core.filetree import FileTree, FileEntry


class _Dummy:
    name = "dummy"

    def detect(self, tree):
        return [Fact(type="dummy.hit", file="x", line=1, data={"k": "v"})]


def test_fact_defaults():
    f = Fact(type="t", file="f", line=2)
    assert f.data == {} and f.evidence == ""


def test_run_detectors_aggregates():
    tree = FileTree("r", [FileEntry("x", "y", 1, False)])
    facts = run_detectors(tree, detectors=[_Dummy()])
    assert facts[0].type == "dummy.hit"
