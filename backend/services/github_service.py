import os, shutil
from git import Repo
from github import Github
from config import GITHUB_TOKEN, CLONE_DIR

g = Github(GITHUB_TOKEN)

def run_contribution(repo_url: str, ai_result: dict, log) -> str:
    name       = repo_url.replace("https://github.com/", "").strip("/")
    local_path = os.path.join(CLONE_DIR, name.replace("/", "_"))

    try:
        log("Cloning repository")
        auth_url   = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        local_repo = Repo.clone_from(auth_url, local_path)

        branch = ai_result["git"].get("branch_name") or "patchpilot/auto"
        log(f"Creating branch: {branch}")
        local_repo.git.checkout("-b", branch)

        for change in ai_result["changes"]:
            full_path = os.path.join(local_path, change["file_path"])
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            if change["change_type"] == "create":
                with open(full_path, "w") as f:
                    f.write(change["replacement_snippet"])
                log(f"Created: {change['file_path']}")

            elif change["change_type"] == "delete":
                if os.path.exists(full_path):
                    os.remove(full_path)
                    log(f"Deleted: {change['file_path']}")
                else:
                    log(f"Delete skipped (not found): {change['file_path']}")

            elif change["change_type"] == "edit":
                with open(full_path, "r") as f:
                    content = f.read()
                content = content.replace(change["original_snippet"], change["replacement_snippet"], 1)
                with open(full_path, "w") as f:
                    f.write(content)
                log(f"Edited: {change['file_path']}")

        local_repo.git.add("--all")
        local_repo.index.commit(ai_result["git"]["commit_message"])
        log("Changes committed")

        local_repo.git.push("origin", branch)
        log("Branch pushed")

        gh_repo = g.get_repo(name)
        pr = gh_repo.create_pull(
            title=ai_result["git"]["pr_title"],
            body=ai_result["git"]["pr_body"],
            head=branch,
            base=gh_repo.default_branch
        )
        log(f"PR opened: {pr.html_url}")
        return pr.html_url

    finally:
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
            log("Local clone deleted")
