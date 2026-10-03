from rest_framework.generics import ListAPIView

from alerts.models import PhishingAlert
from alerts.serializers import PhishingAlertSerializer


class PhishingAlertListView(ListAPIView):
    """List the phishing alerts detected for the caller's enterprise."""

    serializer_class = PhishingAlertSerializer

    def get_queryset(self):
        return PhishingAlert.objects.filter(enterprise=self.request.user.enterprise).order_by(
            "detected_at"
        )
