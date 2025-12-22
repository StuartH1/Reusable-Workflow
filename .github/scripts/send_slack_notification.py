import json
import logging
import os
import sys
from typing import Any, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

github_event = json.loads(os.getenv("GITHUB_EVENT", ""))
actor = os.getenv("GITHUB_ACTOR", "")
slack_bot_token = os.getenv("SLACK_GH_BOT_TOKEN", "")
slack_channel_id = os.getenv("SLACK_CHANNEL_DEVELOPER_NOTIFICATIONS", "")
slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

logger.info(f"GITHUB_EVENT: {github_event}")
pr_object = github_event.get("pull_request")
comment_body = github_event.get("comment", {}).get("body")
comment_pr_number = github_event.get("issue", {}).get("number")
comment_pr_url = github_event.get("issue", {}).get("pull_request", {}).get("html_url")
event_action = github_event.get("action")
event_review_state = github_event.get("review", {}).get("state")
pr_author = pr_object.get("user", {}).get("login")
pr_number = pr_object.get("number")
pr_url = pr_object.get("html_url")
repo_name = github_event.get("repository", {}).get("name")
logger.info(f"PR_OBJECT: {pr_object}")
logger.info(f"PR_URL: {pr_url}")
logger.info(f"PR_NUMBER: {pr_number}")
logger.info(f"PR_AUTHOR: {pr_author}")
logger.info(f"EVENT_ACTION: {event_action}")
logger.info(f"EVENT_REVIEW_STATE: {event_review_state}")
logger.info(f"COMMENT_BODY: {comment_body}")
logger.info(f"COMMENT_PR_NUMBER: {comment_pr_number}")
logger.info(f"COMMENT_PR_URL: {comment_pr_url}")

PR_NUMBER = pr_number if pr_number else comment_pr_number
PR_URL = pr_url if pr_url else comment_pr_url

# Mapping from GitHub username to Slack user ID
user_map = {
    "Blosil12": "U03LE98UKEF",
    "cbradl01": "U02LL8QLL1X",
    "ClaytonFish": "U03M31SG8TF",
    "haydennbps": "U01PNNMJSG0",
    "michaelh-BPS": "U09M1C03PQF",
    "rbecker-ut": "U015F13QURG",
    "StuartH1": "U067BG3JC1K",
    "taranbhagat": "U01125T8GQ0",
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
    return f"{mentions} *{actor_name}* {action} <{PR_URL}|PR #{PR_NUMBER}>."


def has_label(label_name: str) -> bool:
    """Check if the PR has a specific label."""
    labels = pr_object.get("labels", [])
    return any(label.get("name") == label_name for label in labels)


parent_message = find_pr_thread(repo_name, PR_NUMBER)
logger.info(f"PARENT_MESSAGE: {parent_message}")
parent_ts = parent_message["ts"] if parent_message else None

if event_action == "hotfix_approved":
    send_slack(
        f":fire: <{PR_URL}|PR #{PR_NUMBER}> (hotfix) was auto-approved and merged by *{actor}*.",
        parent_ts,
    )
elif event_action == "closed" and pr_object.get("merged"):
    branch = pr_object.get("base", {}).get("ref", "main/master")
    send_slack(
        f":tada: <{pr_url}|PR #{pr_number}> was merged into *{branch}* by *{actor}*.",
        parent_ts,
    )
elif event_review_state == "changes_requested":
    pr_author = get_pr_author()
    send_slack(
        get_message(pr_author, actor, "has requested changes to your "), parent_ts
    )
elif comment_body:
    message = get_message(pr_author, actor, "has commented on ")
    send_slack(message, parent_ts)
elif event_action == "review_requested":
    pr_reviewers = pr_object.get("requested_reviewers")
    slack_pr_reviewers = get_mentions(pr_reviewers)
    if event_review_state == "requested-changes":
        message = get_message(
            slack_pr_reviewers,
            actor,
            "has addressed your requested changes and requested your review again",
        )
    else:
        message = get_message(slack_pr_reviewers, actor, "has requested your review")

    send_slack(message, parent_ts)
elif event_review_state == "approved":
    # Notify the PR author that their PR was approved
    if has_label("hotfix"):
        sys.exit()
    pr_author = get_pr_author()
    message = get_message(pr_author, actor, "has approved your ")
    send_slack(message, parent_ts)


sys.exit()
