from django.http import JsonResponse

from relay.store import load_subscription


def get_subscription(request, subscription_id):
    try:
        subscription = load_subscription(subscription_id)
    except KeyError:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse({"id": subscription.id, "url": subscription.url})
