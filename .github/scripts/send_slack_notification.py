import json
import os
import sys

import requests

# Parse basic environment variables
pr_object = json.loads(os.getenv("PR_OBJECT"))
event_name = os.getenv("GITHUB_EVENT_NAME")
event_review_state = os.getenv("GITHUB_EVENT_REVIEW_STATE")
event_action = os.getenv("GITHUB_EVENT_ACTION")
actor = os.getenv("GITHUB_ACTOR")
pr_url = os.getenv("PR_URL")
pr_number = os.getenv("PR_NUMBER")
pr_info = os.getenv("PR_INFO")
pull_request_review_thread = os.getenv("PULL_REQUEST_REVIEW_THREAD")

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


def send_slack(message: str) -> None:
    """Send a message to the configured Slack webhook."""
    payload = {"text": message, "username": "GitHub Actions", "icon_emoji": ":octocat:"}
    requests.post(os.getenv("SLACK_WEBHOOK_URL"), json=payload)


def get_mentions(reviewers: list[dict]) -> str:
    return " ".join(
        f"<@{user_map[reviewer.get('login')]}>"
        for reviewer in reviewers
        if reviewer.get("login") in user_map
    )


def get_message(mentions: str, actor_name: str, action: str) -> str:
    return f"{mentions} *{actor_name}* {action} <{pr_url}|PR #{pr_number}>."

print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")

print(f"event_review_state: {event_review_state}")
print(f"event_name: {event_name}")
print(f"pull_request_review_thread: {pull_request_review_thread}")

print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")



if event_review_state == "changes_requested" :
    reviewers = pr_object.get("requested_reviewers", [])
    mentions = get_mentions(reviewers)
    send_slack(get_message(mentions, actor, "has requested changes to your PR"))
    sys.exit()

elif event_action == "review_requested":
    reviewers = pr_object.get("requested_reviewers", [])
    mentions = get_mentions(reviewers)
    send_slack(get_message(mentions, actor, "has requested your review"))
    sys.exit()


