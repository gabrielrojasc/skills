import requests

from relay.sender import send_webhook


def deliver(event, subscription):
    """Deliver one event to a subscriber.

    The queue worker gives each delivery a 10-second budget before it marks the
    event as timed out and redelivers it.
    """
    try:
        send_webhook(subscription.url, event.payload)
    except requests.HTTPError as exc:
        if exc.response.status_code in (400, 401, 403, 404, 410):
            subscription.disable(reason=f"permanent {exc.response.status_code}")
        raise
