from relay.models import Subscription


def load_subscription(subscription_id):
    """Load a subscription by ID, or None when it does not exist."""
    return Subscription.objects.filter(pk=subscription_id).first()
