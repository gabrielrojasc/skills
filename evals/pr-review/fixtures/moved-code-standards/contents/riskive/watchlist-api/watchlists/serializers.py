from rest_framework import serializers

from watchlists.models import Watchlist, WatchlistMember


class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watchlist
        fields = ["id", "name", "archived", "created_at"]
        read_only_fields = ["archived", "created_at"]


class BulkArchiveSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class WatchlistMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistMember
        fields = ["id", "watchlist", "name", "added_at"]
