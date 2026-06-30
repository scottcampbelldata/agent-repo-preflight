from __future__ import annotations

_COLOR = {"PASS": "brightgreen", "REVIEW": "yellow", "FAIL": "red"}


def badge_endpoint(verdict: str) -> dict:
    """Build a shields.io endpoint-badge payload for a scan verdict.

    See https://shields.io/badges/endpoint-badge — host the returned JSON and point
    a shields endpoint badge at its raw URL.
    """
    return {
        "schemaVersion": 1,
        "label": "agent-preflight",
        "message": verdict,
        "color": _COLOR.get(verdict, "lightgrey"),
    }
