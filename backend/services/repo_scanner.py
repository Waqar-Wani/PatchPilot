from github import Github
from config import GITHUB_TOKEN

g = Github(GITHUB_TOKEN)

PRIORITY_FILES = [
    "README.md",
    "readme.md",
    "CONTRIBUTING.md",
    "LICENSE",
    ".gitignore",
    ".env",
    ".env.example",
    "SECURITY_FINDINGS.md",
    "exposed_credentials.txt",
]

SENSITIVE_NAME_HINTS = (
    "secret",
    "credential",
    "token",
    "key",
    ".env",
    ".pem",
    ".pfx",
    ".p12",
    ".keystore",
)

def get_file_tree(repo) -> str:
    lines = []
    def walk(path="", depth=0):
        if depth > 3:
            return
        try:
            for item in repo.get_contents(path):
                lines.append("  " * depth + item.path)
                if item.type == "dir":
                    walk(item.path, depth + 1)
        except Exception:
            pass
    walk()
    return "\n".join(lines)

def collect_sensitive_files(repo) -> list:
    """Collect small, potentially sensitive files to surface to the LLM."""
    collected = []

    def walk(path="", depth=0):
        if depth > 3:
            return
        try:
            for item in repo.get_contents(path):
                name = item.path.lower()
                if item.type == "file" and any(h in name for h in SENSITIVE_NAME_HINTS):
                    try:
                        content = item.decoded_content.decode("utf-8", errors="ignore")[:4000]
                        collected.append({"path": item.path, "content": content})
                    except Exception:
                        pass
                if item.type == "dir":
                    walk(item.path, depth + 1)
        except Exception:
            pass

    walk()
    return collected

def get_file(repo, path: str) -> str:
    try:
        return repo.get_contents(path).decoded_content.decode("utf-8", errors="ignore")[:4000]
    except Exception:
        return ""

def build_snapshot(repo_url: str, history: list) -> dict:
    name = repo_url.replace("https://github.com/", "").strip("/")
    repo = g.get_repo(name)

    target_files = [
        {"path": f, "content": get_file(repo, f)}
        for f in PRIORITY_FILES
        if get_file(repo, f)
    ]

    try:
        issues = [i.title for i in repo.get_issues(state="open")][:10]
    except Exception:
        issues = []

    try:
        languages = list(repo.get_languages().keys())
    except Exception:
        languages = []

    file_tree = get_file_tree(repo)
    sensitive_files = collect_sensitive_files(repo)

    # Fallback: if collect_sensitive_files missed but file_tree shows sensitive names, add stubs
    for line in file_tree.splitlines():
        lower = line.lower()
        if any(h in lower for h in SENSITIVE_NAME_HINTS):
            if not any(f["path"].lower() == line.lower() for f in sensitive_files):
                sensitive_files.append({"path": line.strip(), "content": ""})

    return {
        "repo_url":             repo_url,
        "file_tree":            file_tree,
        "readme":               get_file(repo, "README.md"),
        "target_files":         target_files,
        "sensitive_files":      sensitive_files,
        "open_issues":          issues,
        "languages":            languages,
        "contribution_history": history,
    }
