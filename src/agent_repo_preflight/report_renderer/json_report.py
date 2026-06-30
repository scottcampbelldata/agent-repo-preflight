from __future__ import annotations

import json

from ..scanner_core.model import ReportModel


def render_json(report: ReportModel) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=False)
