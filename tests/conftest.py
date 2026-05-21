"""Shared pytest configuration — skips all tests if the API key is not set."""
import pytest
import config


def pytest_collection_modifyitems(items):
    if not config.XAI_API_KEY:
        skip = pytest.mark.skip(
            reason="XAI_API_KEY not configured — run setup_env.py first"
        )
        for item in items:
            item.add_marker(skip)
