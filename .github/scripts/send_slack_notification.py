import json
import os
import sys

import requests

# Parse basic environment variables
pr_object = json.loads(os.getenv("PR_OBJECT", ""))
actor = os.getenv("GITHUB_ACTOR", "")
pr_url = os.getenv("PR_URL", "")
pr_number = os.getenv("PR_NUMBER", "")
event_action = os.getenv("GITHUB_EVENT_ACTION", "")
event_review_state = os.getenv("GITHUB_EVENT_REVIEW_STATE")
pr_author = os.getenv("PR_AUTHOR")

# Mapping from GitHub username to Slack user ID
user_map = {
    "Blosil12": "U03LE98UKEF",
    "cbradl01": "U02LL8QLL1X",
    "StuartH1": "U067BG3JC1K",
    "jake94a": "U03CVABRQNN",
    "JakeBPS": "U0651S1GJK1",
    "rbecker-ut": "U015F13QURG",
    "taranbhagat": "U01125T8GQ0",
    "haydennbps": "U01PNNMJSG0",
    "ClaytonFish": "U03M31SG8TF",
    "zenzenzen": "U04119RP19C",
    "StuartH23": "U067BG3JC1K",
}


def send_slack(message: str) -> None:
    """Send a message to the configured Slack webhook."""
    payload = {"text": message, "username": "GitHub Actions", "icon_emoji": ":octocat:"}
    requests.post(os.getenv("SLACK_WEBHOOK_URL", ""), json=payload)


def get_mentions(reviewers: list[dict]) -> str:
    return " ".join(
        f"<@{user_map[login]}>"
        for reviewer in reviewers
        if (login := reviewer.get("login")) and login in user_map
    )


def get_pr_author() -> str:
    """Get mention for the PR author."""
    return f"<@{user_map[pr_author] if pr_author in user_map else pr_author}>"


def get_message(mentions: str, actor_name: str, action: str) -> str:
    return f"{mentions} *{actor_name}* {action} <{pr_url}|PR #{pr_number}>."


def has_label(label_name: str) -> bool:
    """Check if the PR has a specific label."""
    labels = pr_object.get("labels", [])
    return any(label.get("name") == label_name for label in labels)


if event_review_state == "changes_requested":
    pr_author = get_pr_author()
    send_slack(get_message(pr_author, actor, "has requested changes to your PR"))
    sys.exit()

elif event_action == "review_requested":
    pr_reviewers = pr_object.get("requested_reviewers")
    slack_pr_reviewers = get_mentions(pr_reviewers)
    if has_label("requested-changes"):
        message = get_message(
            slack_pr_reviewers,
            actor,
            "has addressed your requested changes and requested your review again",
        )
    else:
        message = get_message(slack_pr_reviewers, actor, "has requested your review")
    send_slack(message)
    sys.exit()

elif event_review_state == "approved":
    # Notify the PR author that their PR was approved
    pr_author = get_pr_author()
    message = get_message(pr_author, actor, "has approved your PR")
    send_slack(message)
    sys.exit()
