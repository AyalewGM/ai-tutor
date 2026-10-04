"""Suite-wide test fixtures."""

import pytest

from app.core.settings import settings


@pytest.fixture(autouse=True)
def _auth_throttles_off(monkeypatch):
    """Keep auth throttles off for the general suite.

    The shared 'testclient' IP and optional local Redis would otherwise trip
    or break unrelated tests. Edge-security tests re-enable the flag and stub
    Redis explicitly.
    """
    monkeypatch.setattr(settings, "auth_throttles_enabled", False)
