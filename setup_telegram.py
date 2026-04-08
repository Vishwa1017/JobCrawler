"""
Run this once locally to get your Telegram Chat ID.

Steps:
  1. Create a bot: open Telegram → message @BotFather → /newbot → follow prompts
  2. Copy the bot token BotFather gives you
  3. Run: python setup_telegram.py
  4. Paste your token when prompted
  5. Send any message to your new bot in Telegram
  6. This script will print your Chat ID — save it for GitHub Secrets
"""

import time
import requests


def get_chat_id(token: str) -> str | None:
    print("\nWaiting for you to send a message to your bot...")
    print("→ Open Telegram, find your bot, and send it any message (e.g. 'hi')\n")

    url = f"https://api.telegram.org/bot{token}/getUpdates"

    for attempt in range(30):  # Wait up to 60 seconds
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            updates = data.get("result", [])
            if updates:
                chat_id = updates[-1]["message"]["chat"]["id"]
                return str(chat_id)
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(2)
        print(f"  Still waiting... ({attempt + 1}/30)", end="\r")

    return None


def test_notification(token: str, chat_id: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": (
            "✅ <b>JobCrawler is connected!</b>\n\n"
            "You'll receive job alerts here as soon as new positions are posted.\n\n"
            "🇨🇦 Watching: Canada\n"
            "💼 Roles: Backend Engineer / ML / GenAI\n"
            "📊 Level: Entry to Mid"
        ),
        "parse_mode": "HTML",
    }, timeout=10)

    if resp.ok:
        print("\n✅ Test message sent successfully! Check your Telegram.")
    else:
        print(f"\n❌ Failed to send test message: {resp.text}")


def main() -> None:
    print("=" * 50)
    print("  JobCrawler — Telegram Setup")
    print("=" * 50)
    print()

    token = input("Paste your Telegram Bot Token: ").strip()
    if not token:
        print("No token provided. Exiting.")
        return

    # Validate token format
    if ":" not in token or len(token) < 30:
        print("That doesn't look like a valid token. Get it from @BotFather.")
        return

    chat_id = get_chat_id(token)
    if not chat_id:
        print("\n❌ No message received. Make sure you messaged your bot in Telegram.")
        return

    print(f"\n✅ Your Chat ID: {chat_id}")
    print()
    print("=" * 50)
    print("  Add these to GitHub Secrets:")
    print("=" * 50)
    print(f"  TELEGRAM_BOT_TOKEN  =  {token}")
    print(f"  TELEGRAM_CHAT_ID    =  {chat_id}")
    print()

    test_notification(token, chat_id)


if __name__ == "__main__":
    main()
