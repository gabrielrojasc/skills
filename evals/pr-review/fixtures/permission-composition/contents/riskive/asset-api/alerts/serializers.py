from rest_framework import serializers

from alerts.models import Alert


class AlertTriageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["id", "title", "status"]
