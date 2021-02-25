import pytest


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", help="run slow tests")
    parser.addoption("--runlocal", action="store_true", help="run local tests")


def pytest_runtest_setup(item):
    if "slow" in item.keywords and not item.config.getvalue("runslow"):
        pytest.skip("need --runslow option to run")

    if "local" in item.keywords and not item.config.getvalue("runlocal"):
        pytest.skip("need --runlocal option to run")
