"""
AIF369 Backend — Pytest configuration
"""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--deployed-url",
        action="store",
        default=None,
        help="Base URL of deployed service for smoke tests"
    )


@pytest.fixture
def deployed_url(request):
    return request.config.getoption("--deployed-url")
