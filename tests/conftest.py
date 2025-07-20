
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session", autouse=True)
def close_qapplication():
    yield
    # Ensure QApplication is properly closed after tests
    if QApplication.instance():
        QApplication.instance().quit()
