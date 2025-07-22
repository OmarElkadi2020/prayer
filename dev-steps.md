  Proposed Plan

   1. Improve Versioning:
       * The version number is currently hardcoded in build.py. This is prone to errors.
       * Action: I will modify build.py to read the version directly from src/__version__.py. This will create a single, reliable
         source for the version number.
       * Process: I will also introduce the practice of using Git tags (e.g., v1.0.1) to mark specific commits as releases.

   2. Add Documentation (for the Wiki):
       * While I cannot directly edit the GitHub Wiki itself (it's a separate Git repository), I can create high-quality
         documentation in Markdown files within this project. You can then easily copy this content to the Wiki.
       * Action: I will create a docs/ directory and populate it with detailed guides based on the current README.md and other
         project files.
       * Proposed Files:
           * docs/01-installation.md: Detailed installation steps for users and developers.
           * docs/02-configuration.md: In-depth guide on configuring the app, including prayer times, audio, and calendar
             integration.
           * docs/03-usage.md: How to run and interact with the application.
           * docs/04-for-developers.md: Information on the development setup, running tests, and the build process.

   3. Automate Releases on GitHub:
       * I will create a new GitHub Actions workflow to automate the release process.
       * Action: This workflow (.github/workflows/release.yml) will:
           1. Trigger automatically when you push a new tag to main that looks like a version (e.g., v1.1.0).
           2. Build the application for Windows, macOS, and Linux.
           3. Create a GitHub Release, using the tag's name.
           4. Upload the built installers and packages (.exe, .dmg, .deb) as assets to the GitHub Release, making them available
              for download.

   4. Clean Up Git History:
       * Warning: Rewriting the history of a public/shared branch like main is a destructive action. If anyone else has cloned or
         forked this repository, it can cause significant issues for them.
       * Proposed Safe Approach: Instead of rewriting the entire history, I will perform an interactive rebase on a new branch to
         clean up only the most recent commits. This will involve squashing minor fixup commits and improving commit messages to
         be more descriptive.
       * Action:
           1. Create a new branch history-cleanup.
           2. Perform an interactive rebase on that branch to clean up the last 10-15 commits.
           3. Once you approve the cleaned history on that branch, I can guide you on how to safely replace the main branch with
              it.