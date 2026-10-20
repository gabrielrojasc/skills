"""Delivery worker."""

import logging
from datetime import datetime, timezone

import requests

from relay import queue, sender
from relay.backoff import delay_for_attempt, retry_after_delay

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


def process(job):
    """Deliver one queued job, scheduling a retry or giving up on failure."""
    try:
        sender.send_webhook(job.url, job.payload)
    except requests.RequestException as exc:
        if job.attempt >= MAX_ATTEMPTS:
            log.error("giving up on delivery %s after %s attempts: %s", job.id, job.attempt, exc)
            return
        delay = _retry_delay(exc, job.attempt)
        log.warning("delivery %s attempt %s failed: %s; retrying in %.1fs", job.id, job.attempt, exc, delay)
        queue.schedule(job.retry(), delay)


def _retry_delay(exc, attempt):
    if exc.response is not None:
        requested = retry_after_delay(exc.response.headers.get("Retry-After"), datetime.now(timezone.utc))
        if requested is not None:
            return requested
    return delay_for_attempt(attempt)
