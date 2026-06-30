def test_package_imports_and_has_version():
    import agent_repo_preflight
    assert isinstance(agent_repo_preflight.__version__, str)
    assert agent_repo_preflight.__version__
