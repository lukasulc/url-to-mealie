def friendly_title(t):
    return {
        "rate_limit": "Instagram Rate Limit Reached",
        "login_required": "Login Required by Instagram",
        "private_content": "Private Instagram Content",
        "content_unavailable": "Content Not Available",
    }.get(t, "Download Failed")


def friendly_message(t):
    return {
        "rate_limit": "Instagram is temporarily blocking automated access. This is usually temporary.",
        "login_required": "Instagram requires a logged-in session to view this post.",
        "private_content": "The account is private. Media cannot be accessed automatically.",
        "content_unavailable": "This post may be deleted or restricted.",
    }.get(t, "We couldn’t download this video right now.")


def friendly_suggestions(t):
    base = [
        "Try again in 15–30 minutes",
        "You can still add the recipe manually from the post caption",
    ]
    if t == "login_required":
        base.append(
            "If you can open it in the app, copy ingredients/instructions into Mealie"
        )
    if t == "private_content":
        base.append(
            "Follow the account to view it in Instagram, then copy details manually"
        )
    return base
