"""Dates and times in the RM's time zone.

The AWS servers run on UTC, so date.today() there is wrong for Singapore users
between midnight and 08:00 SGT. "Today" and displayed times use APP_TIMEZONE
(default Asia/Singapore); timestamps are still stored in UTC.
"""
import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Singapore")
APP_TIMEZONE_LABEL = os.getenv("APP_TIMEZONE_LABEL", "SGT")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def local_now() -> datetime:
    return _utcnow().astimezone(ZoneInfo(APP_TIMEZONE))


def local_today() -> date:
    return local_now().date()


def format_local(utc_naive, fmt="%d %b %Y, %H:%M") -> str:
    """A naive UTC datetime from the database, shown in local time, e.g. "04 Nov 2026, 03:47 SGT"."""
    if utc_naive is None:
        return "—"
    local = utc_naive.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(APP_TIMEZONE))
    return f"{local.strftime(fmt)} {APP_TIMEZONE_LABEL}"
