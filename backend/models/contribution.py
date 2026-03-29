from datetime import datetime

def new_contribution(repo_url: str, mode: str) -> dict:
    return {
        "repo_url":           repo_url,
        "mode":               mode,
        "status":             "pending",
        "action":             None,
        "skip_reason":        None,
        "pr_url":             None,
        "pr_title":           None,
        "branch":             None,
        "contribution_type":  None,
        "confidence":         None,
        "logs":               [],
        "created_at":         datetime.utcnow(),
        "updated_at":         datetime.utcnow(),
    }
