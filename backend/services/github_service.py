import os, shutil
from git import Repo
from github import Github
from config import GITHUB_TOKEN, CLONE_DIR

g = Github(GITHUB_TOKEN)

def run_contribution(repo_url: str, ai_result: dict, log) -> str:
    name       = repo_url.replace("https://github.com/", "").strip("/")
    local_path = os.path.join(CLONE_DIR, name.replace("/", "_"))
    allowed_deletes = set(ai_result.get("allowed_deletes", []))

    try:
        log("Cloning repository")
        auth_url   = repo_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        local_repo = Repo.clone_from(auth_url, local_path)

        branch = ai_result["git"].get("branch_name") or "patchpilot/auto"
        log(f"Creating branch: {branch}")
        local_repo.git.checkout("-b", branch)

        for change in ai_result["changes"]:
            full_path = os.path.join(local_path, change["file_path"])
            dirpath = os.path.dirname(full_path)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)

            if change["change_type"] == "create":
                content = change["replacement_snippet"]
                if content is None or str(content).strip() == "":
                    raise ValueError(f"Empty content for create: {change['file_path']}")
                with open(full_path, "w") as f:
                    f.write(change["replacement_snippet"])
                log(f"Created: {change['file_path']}")

            elif change["change_type"] == "delete":
                if change["file_path"] not in allowed_deletes:
                    raise ValueError(f"Unsafe delete attempted on {change['file_path']}")
                if os.path.exists(full_path):
                    os.remove(full_path)
                    log(f"Deleted: {change['file_path']}")
                else:
                    log(f"Delete skipped (not found): {change['file_path']}")

            elif change["change_type"] == "edit":
                new_content = change.get("replacement_snippet")
                if new_content is None or str(new_content).strip() == "":
                    raise ValueError(f"Empty content for edit: {change['file_path']}")
                with open(full_path, "r") as f:
                    content = f.read()
                original = change.get("original_snippet")
                if original is None:
                    raise ValueError(f"Missing original_snippet for edit: {change['file_path']}")
                if original not in content and original.strip() != "":
                    raise ValueError(f"Original snippet not found in {change['file_path']}")
                if original == "":
                    updated = content + ("\n" if not content.endswith("\n") else "") + change["replacement_snippet"]
                else:
                    updated = content.replace(original, change["replacement_snippet"], 1)
                if updated == content:
                    raise ValueError(f"No change applied to {change['file_path']}")
                with open(full_path, "w") as f:
                    f.write(updated)
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
