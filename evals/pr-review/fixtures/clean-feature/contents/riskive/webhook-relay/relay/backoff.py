"""Retry delays for failed deliveries."""

import random
from datetime import timezone
from email.utils import parsedate_to_datetime

BASE_DELAY = 1.0
MAX_DELAY = 60.0


def delay_for_attempt(attempt):
    """Exponential backoff with full jitter, capped at MAX_DELAY."""
    return random.uniform(0, min(MAX_DELAY, BASE_DELAY * 2 ** (attempt - 1)))


def retry_after_delay(header, now):
    """Seconds a Retry-After header asks to wait, capped at MAX_DELAY, or None if it is missing or unreadable."""
    if header is None:
        return None
    value = header.strip()
    if value.isdecimal():
        seconds = float(value)
    else:
        try:
            when = parsedate_to_datetime(value)
        except ValueError:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        seconds = (when - now).total_seconds()
    return min(max(seconds, 0.0), MAX_DELAY)
