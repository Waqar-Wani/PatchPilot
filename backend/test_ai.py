"""
Quick smoke test for the OpenRouter-backed AI client.

Usage:
  cd backend
  source .venv/bin/activate
  python test_ai.py
"""

import json
from pathlib import Path
from services.ai_service import analyze_repo


def main() -> None:
    # Minimal realistic repo snapshot (keeps tokens/cost low but exercises real flow)
    snapshot = {
        "repo_url": "https://github.com/example/example",
        "file_tree": "README.md\nsrc/app.py\ntests/test_app.py",
        "readme": "# Example App\n\nA tiny example project.\n\n## TODO\n- add CI\n- improve docs\n",
        "target_files": [
            {"path": "README.md", "content": "# Example App\nA tiny example project.\n"}
        ],
        "open_issues": ["Add CI workflow", "Improve documentation"],
        "languages": ["Python"],
        "contribution_history": [],
    }

    print("Sending repo snapshot to model via OpenRouter...")
    response = analyze_repo(snapshot)

    print("\nRaw response:\n")
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
