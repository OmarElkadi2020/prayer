
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    """Fixture for QApplication instance, created once per session."""
    app = QApplication.instance() or QApplication([])
    yield app
    app.quit()
