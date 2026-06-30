from agent_repo_preflight.report_renderer.badge import badge_endpoint


def test_pass_badge_is_green():
    b = badge_endpoint("PASS")
    assert b["schemaVersion"] == 1
    assert b["label"] == "agent-preflight"
    assert b["message"] == "PASS"
    assert b["color"] == "brightgreen"


def test_review_badge_is_yellow():
    assert badge_endpoint("REVIEW")["color"] == "yellow"


def test_fail_badge_is_red():
    assert badge_endpoint("FAIL")["color"] == "red"


def test_unknown_verdict_is_grey():
    b = badge_endpoint("WHATEVER")
    assert b["color"] == "lightgrey"
    assert b["message"] == "WHATEVER"
