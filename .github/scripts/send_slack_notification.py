import json
import os
import sys
from typing import Any, Optional

import requests

# Parse basic environment variables
pr_object = json.loads(os.getenv("PR_OBJECT", ""))
actor = os.getenv("GITHUB_ACTOR", "")
pr_url = os.getenv("PR_URL", "")
pr_number = os.getenv("PR_NUMBER", "")
event_action = os.getenv("GITHUB_EVENT_ACTION", "")
event_review_state = os.getenv("GITHUB_EVENT_REVIEW_STATE")
pr_author = os.getenv("PR_AUTHOR", "")
repo_name = os.getenv("REPO_NAME", "")
slack_bot_token = os.getenv("SLACK_GH_BOT_TOKEN", "")
slack_channel_id = os.getenv("SLACK_CHANNEL_ID", "")
slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
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
}


def send_slack(message: str, ts: Optional[str] = None) -> None:
    """Send a message to the configured Slack webhook."""
    payload = {"text": message, "username": "GitHub Actions", "icon_emoji": ":octocat:"}
    if ts:
        payload["thread_ts"] = ts
    requests.post(slack_webhook_url, json=payload)


def find_pr_thread(
    repo_name: str, pr_number: str, bot_id: str = "B06GW8TTWUD"
) -> dict[str, Any] | None:
    """Find the parent review request message and related messages for this PR."""
    headers = {
        "Authorization": f"Bearer {slack_bot_token}",
        "Content-Type": "application/json",
    }
    params: dict[str, Any] = {"channel": slack_channel_id, "limit": 50}
    response = requests.get(
        "https://slack.com/api/conversations.history", headers=headers, params=params
    )
    parent_message = None

    for message in response.json()["messages"]:
        if message.get("bot_id") != bot_id:
            continue
        if f"#{pr_number}" not in message.get("text", ""):
            continue
        if repo_name not in message.get("text", ""):
            continue
        if "has requested your review" in message.get("text", ""):
            parent_message = message
            break

    return parent_message


def notify_slack_on_main_merge(pr_number: str) -> None:
    send_slack(
        f":tada: <{pr_url}|PR #{pr_number}> was merged into *main* by *{actor}* (originally opened by *{pr_author}*)."
    )


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


if event_action == "closed" and pr_object.get("merged"):
    notify_slack_on_main_merge(pr_number)
    print("PR merged into main")
    sys.exit()
elif event_review_state == "changes_requested":
    pr_author = get_pr_author()
    parent_message = find_pr_thread(repo_name, pr_number)
    send_slack(
        get_message(pr_author, actor, "has requested changes to your PR"),
        parent_message["ts"] if parent_message else None,
    )
    print("PR author requested changes")
    sys.exit()
elif event_action == "review_requested":
    pr_reviewers = pr_object.get("requested_reviewers")
    print("review_requested")
    slack_pr_reviewers = get_mentions(pr_reviewers)
    parent_message = None
    if has_label("requested-changes"):
        parent_message = find_pr_thread(repo_name, pr_number)
        message = get_message(
            slack_pr_reviewers,
            actor,
            "has addressed your requested changes and requested your review again",
        )
    else:
        print("no label")
        message = get_message(slack_pr_reviewers, actor, "has requested your review")

    send_slack(message, parent_message["ts"] if parent_message else None)
    sys.exit()
elif event_review_state == "approved":
    # Notify the PR author that their PR was approved
    if has_label("hotfix"):
        sys.exit()
    pr_author = get_pr_author()
    parent_message = find_pr_thread(repo_name, pr_number)
    print("approved")
    message = get_message(pr_author, actor, "has approved your PR")
    send_slack(message, parent_message["ts"] if parent_message else None)
    sys.exit()
