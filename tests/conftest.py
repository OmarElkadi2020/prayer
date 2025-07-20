import os
import sys
import pytest


def pytest_sessionfinish(session, exitstatus):
    """Handle session teardown and optional forced exit."""
    env_force_exit = os.getenv("PYTEST_FORCE_EXIT")
    if env_force_exit:
        if env_force_exit.lower() in {"1", "true", "yes"}:
            # Prefer pytest.exit for a clean teardown
            pytest.exit("forced exit", returncode=exitstatus)
        elif env_force_exit.lower() in {"sys"}:
            # Use sys.exit explicitly when requested
            sys.exit(exitstatus)

