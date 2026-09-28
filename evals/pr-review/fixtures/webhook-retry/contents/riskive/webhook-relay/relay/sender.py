import time

import requests

MAX_ATTEMPTS = 3


def send_webhook(url, payload):
    """Send a webhook."""
    for attempt in range(MAX_ATTEMPTS):
        response = requests.post(url, json=payload, timeout=5)
        # Only retry when the receiver is temporarily unavailable.
        if response.status_code < 400:
            return response
        time.sleep(2 ** attempt)
    response.raise_for_status()
    return response
