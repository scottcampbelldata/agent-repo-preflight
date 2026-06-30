from __future__ import annotations

from typing import Protocol

from ..facts import Fact
from ..filetree import FileTree


class Detector(Protocol):
    name: str

    def detect(self, tree: FileTree) -> list[Fact]: ...


ALL_DETECTORS: list[Detector] = []  # populated by register() calls in detector modules


def register(detector: Detector) -> Detector:
    ALL_DETECTORS.append(detector)
    return detector


def run_detectors(tree: FileTree, detectors: list[Detector] | None = None) -> list[Fact]:
    facts: list[Fact] = []
    for d in detectors if detectors is not None else ALL_DETECTORS:
        facts.extend(d.detect(tree))
    return facts
