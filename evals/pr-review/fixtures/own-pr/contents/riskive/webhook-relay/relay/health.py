import requests


def receiver_is_reachable(url):
    """Whether the receiver answers a HEAD request without a server error."""
    try:
        response = requests.head(url)
    except requests.RequestException:
        return False
    return response.status_code < 500
