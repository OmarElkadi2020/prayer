Work Plan: Architectural Refactoring

  Phase 1: Enhance Testability (Critical Priority)
   * Goal: Decouple business logic from the UI to eliminate testing-related segmentation faults and enable reliable, independent testing of core logic.
   * Tasks:
       1. Refactor `focus_steps.py`:
           * I will create a new FocusStepsPresenter class to contain the core logic for managing steps, content, and state.
           * The existing StepWindow in gui.py will be refactored into a thin "View" component, responsible only for displaying the state managed by
             the presenter and forwarding user events to it.
       2. Refactor `scheduler.py`:
           * I will analyze the scheduler's methods to identify logic that is tightly coupled to the GUI.
           * This logic will be extracted into separate, testable components, leaving the scheduler's methods as minimal wrappers.
       3. Create Unit Tests:
           * I will write new pytest tests for the FocusStepsPresenter and other extracted components. These tests will be pure Python, with no Qt
             dependencies, ensuring they are fast and stable.

  Phase 2: Dependency Injection & Configuration Management
   * Goal: Reduce coupling, improve modularity, and make configuration safer and more robust.
   * Tasks:
       1. Introduce Dependency Injection (DI):
           * I will modify component constructors (like PrayerScheduler) to accept their dependencies (like audio players or calendar services) as
             arguments, instead of relying on global accessors.
           * A central "Composition Root" will be established in src/__main__.py to instantiate and connect all major application components.
       2. Enhance Configuration:
           * I will add pydantic to the project to define a clear configuration schema, ensuring all loaded settings are valid.
           * The configuration system will be updated to load sensitive data (e.g., API keys) from environment variables first, falling back to
             file-based configuration only if necessary.

  Phase 3: Error Handling & Concurrency
   * Goal: Make the application more resilient to failures and clarify its concurrency model.
   * Tasks:
       1. Implement Robust Error Handling:
           * I will establish a global exception handler for the QApplication to catch, log, and report any uncaught errors gracefully.
           * I will define and use custom exception types (e.g., CalendarSyncError) for more precise error handling.
       2. Clarify Threading Model:
           * I will review all background operations to ensure any code that updates the GUI is correctly and safely executed on the main Qt thread.
           * I will add documentation to clarify the application's threading strategy for future development.