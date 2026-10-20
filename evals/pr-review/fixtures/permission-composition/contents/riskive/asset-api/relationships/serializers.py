from rest_framework import serializers

from assets.models import Asset
from relationships.models import Relationship, RelationshipType


class RelationshipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationshipType
        fields = ["id", "name"]


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relationship
        fields = ["id", "parent", "child", "type"]


class RelationshipCreateSerializer(serializers.Serializer):
    parent = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all())
    child = serializers.PrimaryKeyRelatedField(queryset=Asset.objects.all())
    type = serializers.PrimaryKeyRelatedField(queryset=RelationshipType.objects.all())
