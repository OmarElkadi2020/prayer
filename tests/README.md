# Testing Framework for Prayer Player

This document outlines the testing strategy and best practices for the Prayer Player application. The goal is to ensure code quality, maintainability, and resilience against changes and external dependencies.

## 1. Philosophy

Our testing approach emphasizes:
*   **Unit Tests**: Isolating and testing individual functions, methods, or classes in isolation. These tests should be fast and cover specific logic.
*   **Integration Tests**: Verifying the interactions between different components or modules. This includes testing interactions with external services (e.g., Aladhan API, Google Calendar) using controlled mocks.
*   **End-to-End (E2E) Tests**: (Future consideration) Simulating real user scenarios to ensure the entire application flow works as expected.

## 2. Directory Structure

The `tests/` directory is organized as follows:

```
tests/
├── __init__.py
├── conftest.py             # Shared fixtures, hooks, and configurations
├── test_actions.py         # Tests for src/prayer/actions.py (enhanced audio playback tests)
├── test_config.py          # Tests for src/prayer/config/security/__init__.py (enhanced config loading/saving tests)
├── test_focus_steps.py     # Tests for src/prayer/focus_steps.py
├── test_main_cli.py        # Tests for src/prayer/__main__.py (CLI entry point and dry-run)
├── test_prayer_times.py    # Tests for src/prayer/prayer_times.py (enhanced error handling)
├── test_scheduler_unit.py  # Unit tests for src/prayer/scheduler.py
├── test_scheduler.py       # Additional scheduler tests (now uses mocked calendar service)
├── test_google_calendar.py # Unit tests for src/prayer/calendar_api/google_calendar.py
├── test_calendar_utils.py  # Unit tests for src/prayer/calendar_utils.py
├── test_gui.py             # GUI tests for src/prayer/gui.py
├── test_service.py         # Tests for src/prayer/platform/service.py
└── ...
```

## 3. Running Tests

We use `pytest` as our testing framework.

To run all tests:
```bash
pytest
```

To run tests in a specific file:
```bash
pytest tests/test_scheduler.py
```

To run tests matching a keyword expression:
```bash
pytest -k "scheduler and dry_run"
```

To see more detailed output (e.g., print statements during tests):
```bash
pytest -s
```

### Incremental Testing with `pytest-incremental`

`pytest-incremental` is integrated to speed up test runs by only executing tests that are affected by recent code changes or that previously failed. This avoids re-running successful, unrelated tests.

To use it, simply run `pytest` as usual:
```bash
pytest
```

If you need to force all tests to run, use the `--incremental-force` flag:
```bash
pytest --incremental-force
```

## 4. Best Practices for Writing Tests

*   **Clear Naming**: Test files should start with `test_` or end with `_test.py`. Test functions should start with `test_`.
*   **Single Responsibility**: Each test function should ideally test one specific aspect or scenario.
*   **Arrange-Act-Assert (AAA)**: Structure your tests clearly:
    1.  **Arrange**: Set up the test environment, inputs, and mocks.
    2.  **Act**: Execute the code under test.
    3.  **Assert**: Verify the expected outcome.
*   **Use Fixtures**: Leverage `conftest.py` to define reusable setup/teardown logic and test data. This reduces duplication and improves maintainability.
*   **Mock External Dependencies**: For integration tests, use `unittest.mock` or `pytest-mock` to mock external services (APIs, databases, calendar services) to ensure tests are fast, reliable, and isolated from network issues or external state.

## 5. Mocking External Services

When testing components that interact with external APIs (e.g., Aladhan API, Google Calendar API), it's crucial to mock these interactions to ensure tests are deterministic and fast.

*   **Aladhan API**: Mock `requests.get` calls in `prayer_times.py` to return predefined JSON responses.
*   **Google Calendar API**: Mock `googleapiclient.discovery.build` and its subsequent method calls (`events().list()`, `events().insert()`, etc.) in `google_calendar.py` to simulate API responses.
*   **`appdirs`**: Mock `appdirs.user_data_dir` to control where test configuration files are created.

Example of mocking `requests.get` (using `pytest-mock`'s `mocker` fixture):

```python
def test_prayer_times_fetch_success(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "data": {
            "timings": {
                "Fajr": "05:00",
                "Dhuhr": "12:00",
                "Asr": "15:00",
                "Maghrib": "18:00",
                "Isha": "20:00",
                "Sunrise": "06:30",
                # ... other timings
            }
        }
    }
    mocker.patch('requests.Session.get', return_value=mock_response)

    # Now call the function that uses requests.get
    times = today_times("London", "UK")
    assert "Fajr" in times
    assert times["Fajr"].hour == 5
```

## 6. Test Data

Keep test data minimal and representative. For complex data structures, consider using factories (e.g., `factory_boy`) or simple dictionaries/lists defined within `conftest.py` or dedicated test data modules.

## 7. Continuous Integration

Tests should be run automatically as part of the Continuous Integration (CI) pipeline to catch regressions early. (Refer to `.github/workflows/build.yml` for CI configuration).
