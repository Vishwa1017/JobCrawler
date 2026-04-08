import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_job_alert(job: dict) -> bool:
    """Send a single job alert to Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[notifier] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False

    level_tag = job.get("level", "").upper()
    level_line = f"📊 <b>Level:</b> {level_tag}\n" if level_tag else ""

    message = (
        f"🆕 <b>New Job Alert!</b>\n\n"
        f"💼 <b>{job['title']}</b>\n"
        f"🏢 {job['company']}\n"
        f"📍 {job['location']}\n"
        f"🔗 <a href=\"{job['url']}\">Apply Here</a>\n"
        f"{level_line}"
        f"📡 Source: {job['source']}"
    )

    resp = requests.post(
        TELEGRAM_API.format(token=token),
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=10,
    )

    if not resp.ok:
        print(f"[notifier] Telegram error: {resp.status_code} {resp.text}")

    return resp.ok


def send_summary(total_new: int) -> None:
    """Send a summary message when the run finds no new jobs."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    if total_new == 0:
        message = "✅ Crawl complete — no new jobs found this run."
    else:
        message = f"✅ Crawl complete — sent <b>{total_new}</b> new job alert(s)."

    requests.post(
        TELEGRAM_API.format(token=token),
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
        timeout=10,
    )
