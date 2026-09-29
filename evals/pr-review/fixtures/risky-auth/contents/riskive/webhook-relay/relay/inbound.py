from relay.signature import verify_request


def handle_inbound(request, subscription):
    """Accept an event pushed by a partner and forward it to the subscriber.

    Relies on verify_request raising on a bad signature; the return value is not checked.
    """
    verify_request(request, subscription.secret)
    subscription.forward(request.json())
