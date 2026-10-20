from rest_framework import viewsets

from watchlists.models import Watchlist
from watchlists.serializers import WatchlistSerializer


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer

    def get_queryset(self):
        return Watchlist.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)
