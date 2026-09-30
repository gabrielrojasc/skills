import requests


def deliver(event, subscription):
    """Deliver one event to a subscriber."""
    response = requests.post(subscription.url, json=event.payload, timeout=5)
    response.raise_for_status()
