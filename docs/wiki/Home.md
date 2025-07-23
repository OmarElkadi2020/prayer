# Welcome to the Prayer Player Developer Wiki!

This wiki provides a comprehensive overview of the Prayer Player application's architecture, design, and workflow. It is intended for developers who want to contribute to the project or understand its internal workings.

## High-Level Overview

The application follows a decoupled, event-driven architecture centered around a **Scheduler**. The core logic is separated from the GUI, platform-specific features, and external service integrations. This design enhances testability, maintainability, and extensibility.

The main architectural patterns and components are:

1.  **Composition Root**: A single entry point (`__main__.py`) initializes and wires together all the major components.
2.  **Scheduler-based Core**: The central logic is driven by `apscheduler`, which triggers events at specific times.
3.  **Decoupled GUI**: The user interface is built with PySide6 (Qt) and is separated into distinct, independent windows. Communication with the backend happens via an event bus.
4.  **Strategy Pattern for Actions**: A protocol (`ActionExecutor`) is used to decouple the scheduler from the actual implementation of actions (e.g., playing sound), allowing for easy dry-run simulations.
5.  **Service Abstraction**: External services (like Google Calendar) and platform features (like startup services) are accessed through abstraction layers, hiding implementation details.

## Navigation

-   **[Application Workflow](Application-Workflow.md)**: A step-by-step description of how the application runs.
-   **[Component Breakdown](Component-Breakdown.md)**: A detailed look at the individual components and their responsibilities.
-   **[Event-Driven Architecture](Event-Driven-Architecture.md)**: An explanation of the event-driven design and the key events used for communication.
