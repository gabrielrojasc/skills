from rest_framework import mixins, viewsets

from alerts.feature_flags import ALERT_TRIAGE_BETA
from alerts.models import Alert
from alerts.serializers import AlertTriageSerializer
from core.permissions import DEFAULT_GATES, OPAScoped, RequireFeatureFlag

TRIAGE_SCOPE = "alerts:triage"


class AlertTriageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [*DEFAULT_GATES, OPAScoped(TRIAGE_SCOPE) | RequireFeatureFlag(ALERT_TRIAGE_BETA)]
    serializer_class = AlertTriageSerializer

    def get_queryset(self):
        return Alert.objects.filter(company=self.request.user.company)
