PROGRAMMING, EMAIL, CHAT, DOCUMENT, GENERAL = "programming", "email", "chat", "document", "general"

PROCESS_CATEGORIES = {
    "code.exe": PROGRAMMING, "cursor.exe": PROGRAMMING, "windsurf.exe": PROGRAMMING,
    "idea64.exe": PROGRAMMING, "pycharm64.exe": PROGRAMMING, "webstorm64.exe": PROGRAMMING,
    "rider64.exe": PROGRAMMING, "clion64.exe": PROGRAMMING, "goland64.exe": PROGRAMMING,
    "devenv.exe": PROGRAMMING, "sublime_text.exe": PROGRAMMING, "windowsterminal.exe": PROGRAMMING,
    "outlook.exe": EMAIL, "olk.exe": EMAIL, "thunderbird.exe": EMAIL,
    "teams.exe": CHAT, "ms-teams.exe": CHAT, "slack.exe": CHAT, "discord.exe": CHAT,
    "whatsapp.exe": CHAT, "telegram.exe": CHAT, "signal.exe": CHAT,
    "winword.exe": DOCUMENT, "notion.exe": DOCUMENT, "obsidian.exe": DOCUMENT,
    "notepad.exe": DOCUMENT, "wordpad.exe": DOCUMENT,
}

BROWSERS = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "arc.exe", "vivaldi.exe"}

# Window-title hints, used for browsers (web apps) and as a fallback.
TITLE_HINTS = [
    (EMAIL, ("gmail", "outlook", "mail -", "proton mail", "yahoo mail")),
    (CHAT, ("slack", "discord", "microsoft teams", "whatsapp", "messenger", "telegram")),
    (DOCUMENT, ("google docs", "notion", "word", "confluence", "dropbox paper")),
    (PROGRAMMING, ("github", "gitlab", "stack overflow", "codesandbox", "replit", "colab", "jupyter")),
]


def categorize(process: str, title: str) -> str:
    process, title = (process or "").lower(), (title or "").lower()
    if process in PROCESS_CATEGORIES and process not in BROWSERS:
        return PROCESS_CATEGORIES[process]
    for category, hints in TITLE_HINTS:
        if any(h in title for h in hints):
            return category
    return GENERAL
