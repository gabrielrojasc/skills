"""Webhook delivery."""

import requests

HEADERS = {"User-Agent": "webhook-relay"}


def send_webhook(url, payload):
    response = requests.post(url, json=payload, headers=HEADERS, timeout=5)
    response.raise_for_status()
    return response
