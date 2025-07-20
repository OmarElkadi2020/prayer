
import pytest
from PySide6.QtWidgets import QApplication
from unittest.mock import patch

@pytest.fixture(scope="session", autouse=True)
def mock_qapplication(qapp):
    with patch('PySide6.QtWidgets.QApplication', return_value=qapp):
        yield

@pytest.fixture(scope="session", autouse=True)
def close_qapplication():
    yield
    # Ensure QApplication is properly closed after tests
    if QApplication.instance():
        QApplication.instance().quit()
