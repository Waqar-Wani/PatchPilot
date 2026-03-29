# Security Findings

- Removed `exposed_credentials.txt` that contained dummy AWS keys and Slack token used for testing.
- Added `exposed_credentials.txt` to `.gitignore` to prevent future commits of secret files.

Recommendation: rotate any real credentials if they were ever committed, and enable secret scanning in GitHub.

Note: This file has been permanently removed from the repository.
