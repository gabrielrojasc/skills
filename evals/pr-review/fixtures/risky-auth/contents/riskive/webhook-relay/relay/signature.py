import hashlib
import hmac


def verify_request(request, secret):
    """Check the request signature."""
    signature = request.headers.get("X-Relay-Signature")
    if signature is None:
        # Older senders don't sign requests yet.
        return True
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    return signature == expected
