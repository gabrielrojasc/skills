from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from relay.auth import staff_required
from relay.health import receiver_is_reachable
from relay.models import Subscription


@require_POST
@staff_required
def activate_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    if not receiver_is_reachable(subscription.url):
        return JsonResponse({"error": "receiver unreachable"}, status=422)
    subscription.active = True
    subscription.save(update_fields=["active"])
    return JsonResponse({"id": subscription.id, "active": True})
