import os
import requests
from datetime import datetime, timezone

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _time_ago(iso_str: str) -> str:
    try:
        posted = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        diff = datetime.now(timezone.utc) - posted
        mins = int(diff.total_seconds() / 60)
        if mins < 1:
            return "just now"
        if mins < 60:
            return f"{mins} min ago"
        return f"{mins // 60}h {mins % 60}m ago"
    except Exception:
        return "recently"


def send_job_alert(job: dict) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[notifier] Missing credentials")
        return False

    posted_label = _time_ago(job.get("posted", ""))

    sep = "-" * 30
    message = (
        f"<b>Job Alert</b>\n"
        f"{sep}\n"
        f"<b>Role</b>      {job['title']}\n"
        f"<b>Company</b>   {job['company']}\n"
        f"<b>Location</b>  {job['location']}\n"
        f"<b>Posted</b>    {posted_label}\n"
        f"<b>Source</b>    {job['source']}\n"
        f"{sep}\n"
        f"<a href=\"{job['url']}\">View and Apply</a>"
    )

    resp = requests.post(
        TELEGRAM_API.format(token=token),
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )
    return resp.ok


def send_summary(total_new: int) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    msg = (
        f"Scan complete — {total_new} new job(s) found."
        if total_new > 0
        else "Scan complete — no new jobs in the last hour."
    )

    requests.post(
        TELEGRAM_API.format(token=token),
        json={"chat_id": chat_id, "text": msg},
        timeout=10,
    )
