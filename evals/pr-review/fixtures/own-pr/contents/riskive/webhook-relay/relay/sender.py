"""Webhook delivery."""

import requests


def send_webhook(url, payload):
    response = requests.post(url, json=payload, timeout=5)
    response.raise_for_status()
    return response
