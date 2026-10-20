from rest_framework import viewsets

from watchlists.models import WatchlistMember
from watchlists.serializers import WatchlistMemberSerializer


class WatchlistMemberViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WatchlistMemberSerializer

    def get_queryset(self):
        return WatchlistMember.objects.filter(watchlist__organization=self.request.user.organization)
