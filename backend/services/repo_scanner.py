from github import Github
from config import GITHUB_TOKEN

g = Github(GITHUB_TOKEN)

PRIORITY_FILES = [
    "README.md", "readme.md", "CONTRIBUTING.md", "LICENSE", ".gitignore"
]

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

    return {
        "repo_url":             repo_url,
        "file_tree":            get_file_tree(repo),
        "readme":               get_file(repo, "README.md"),
        "target_files":         target_files,
        "open_issues":          issues,
        "languages":            languages,
        "contribution_history": history,
    }
