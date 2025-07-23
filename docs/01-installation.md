# Installation

Installing Prayer Player is straightforward. We provide pre-built installers for Windows, macOS, and Linux, which is the recommended method for most users. For developers who wish to run the application from source, a manual setup process is also available.

## Recommended Installation (for End-Users)

The easiest way to get started is to download the latest installer for your operating system from our [**GitHub Releases**](https://github.com/Omar-Elawady/prayer-player/releases) page.

| Operating System | File Type         |
| :--------------- | :---------------- |
| **Windows**      | `.exe` (Installer) |
| **macOS**        | `.dmg` (Disk Image)|
| **Linux**        | `.deb` (Debian Pkg) |

Simply run the downloaded installer and follow the on-screen instructions. The installer will handle all dependencies and set up the application to be easily accessible on your system.

## Developer Installation (from Source)

If you are a developer and want to run the application directly from the source code, follow these steps.

### Prerequisites

-   [Python 3.8+](https://www.python.org/downloads/)
-   [Git](https://git-scm.com/downloads)

### Steps

1.  **Clone the Repository:**
    Open your terminal or command prompt and clone the project repository:
    ```bash
    git clone https://github.com/Omar-Elawady/prayer-player.git
    cd prayer-player
    ```

2.  **Run the Installer Script:**
    The project includes a Python script that automates the setup process. It creates a virtual environment to isolate dependencies and installs all required packages.
    ```bash
    python installer.py
    ```
    This script will:
    -   Create a `myenv` directory containing the Python virtual environment.
    -   Install all packages listed in `requirements.txt`.
    -   Prepare the application to be run from the command line.

Once the script finishes, your development environment is ready. You can now run the application as described in the [**Usage**](03-usage.md) guide.
