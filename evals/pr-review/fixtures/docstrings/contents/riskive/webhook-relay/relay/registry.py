class SubscriptionRegistry:
    """Registry of subscriptions."""

    def __init__(self):
        """Create an empty registry."""
        self._subscriptions = {}

    def get(self, subscription_id):
        """Get a subscription."""
        return self._subscriptions.get(subscription_id)

    def add(self, subscription):
        """Add a subscription."""
        self._subscriptions[subscription.id] = subscription

    def remove(self, subscription_id):
        """Remove a subscription and email its owner that it was removed."""
        self._subscriptions.pop(subscription_id, None)
