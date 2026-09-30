from relay.delivery import deliver
from relay.store import load_subscription


def fan_out(event, subscription_ids):
    """Deliver an event to each subscriber."""
    for subscription_id in subscription_ids:
        try:
            subscription = load_subscription(subscription_id)
        except KeyError:
            # Deleted since the event was queued.
            continue
        deliver(event, subscription)
