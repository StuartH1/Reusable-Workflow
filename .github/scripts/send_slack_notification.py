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
print(f"pr_info: {pr_info}")
print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")
print("########################################################")
print(f"event_name: {event_name}")
print(f"event_action: {event_action}")
print(f"actor: {actor}")
print(f"pr_url: {pr_url}")
print(f"pr_number: {pr_number}")


reviewers = pr_object.get("requested_reviewers", [])
print(f"reviewers: {reviewers}")
repo = os.getenv("GITHUB_REPOSITORY")
print(f"repo: {repo}")
github_token = os.getenv("GITHUB_TOKEN")
print(f"github_token: {github_token}")
print("########################################################")
print("########################################################")
print("########################################################")



if event_review_state == "changes_requested" :
    reviewers = pr_object.get("requested_reviewers", [])
    mentions = get_mentions(reviewers)
    send_slack(get_message(mentions, actor, "requested changes on"))
    sys.exit()

if event_name == "pull_request" and event_action == "review_requested":
    # Get reviewers, token, and repo.
    reviewers = pr_object.get("requested_reviewers", [])
    github_token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv(
        "GITHUB_REPOSITORY", ""  
    )

    # Attempt to enhance notifications if a GitHub token is available.
    if github_token and repo and pr_number:
        try:
            # Fetch review history to check if this is a re-review after changes requested
            api_headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            reviews_url = (
                f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
            ) 
            reviews_response = requests.get(reviews_url, headers=api_headers)

            # Check if the review history was fetched successfully
            if reviews_response.status_code != 200:
                print(f"Error fetching review history: {reviews_response.status_code}")
                sys.exit()

            # Group reviews by reviewer for easier processing
            reviewer_history = {}
            for review in reviews_response.json():
                login = review.get("user", {}).get("login")
                if login:
                    reviewer_history.setdefault(login, []).append(review)

            # Identify reviewers who previously requested changes
            changes_addressed_reviewers = []
            for reviewer in reviewers:
                login = reviewer.get("login")
                if login in reviewer_history:
                    # Get the most recent review for this user.
                    last_review = sorted(
                        reviewer_history[login],
                        key=lambda r: r.get("submitted_at", ""),
                        reverse=True,
                    )[0]
                    if last_review.get("state") == "CHANGES_REQUESTED":
                        changes_addressed_reviewers.append(reviewer)

            # Send notification for addressed changes
            if mentions := get_mentions(changes_addressed_reviewers):
                text = "has addressed your requested changes and re-requested your review on"
                send_slack(get_message(mentions, actor, text))
                sys.exit()

        except Exception as e:
            print(f"Error fetching review history: {e}")

    # Send the default review request message.
    if mentions := get_mentions(reviewers):
        send_slack(get_message(mentions, actor, "requested your review on"))


elif event_name == "pull_request_review" and event_action == "submitted":
    review_state = os.getenv("GITHUB_EVENT_REVIEW_STATE", "").lower()

    # Check if the actor is in the user_map.
    if actor not in user_map:
        print(f"Actor {actor} not in user_map")
        sys.exit()

    # Check if the PR author is in the user_map.
    pr_author = pr_object.get("user", {}).get("login")
    if pr_author not in user_map:
        print(f"PR author {pr_author} not in user_map")
        sys.exit()

    # Notify PR author when changes are requested
    if review_state == "changes_requested":
        message = get_message(
            f"<@{user_map[pr_author]}>", actor, "requested changes on"
        )
    elif review_state == "approved":
        message = get_message(f"<@{user_map[pr_author]}>", actor, "approved")
    elif review_state == "commented":
        message = get_message(f"<@{user_map[pr_author]}>", actor, "commented on")
    else:
        print(f"Unknown review state: {review_state}")
        sys.exit()
    send_slack(message)


elif event_name == "pull_request_review_comment" and event_action == "created":
    # TODO: will this ping the channel for every comment?

    # Check if the PR author is in the user_map.
    pr_author = pr_object.get("user", {}).get("login")
    if pr_author not in user_map:
        print(f"PR author {pr_author} not in user_map")
        sys.exit()

    # Notify PR author of new comments (unless they commented on their own PR)
    if pr_author != actor:
        send_slack(get_message(f"<@{user_map[pr_author]}>", actor, "commented on"))
