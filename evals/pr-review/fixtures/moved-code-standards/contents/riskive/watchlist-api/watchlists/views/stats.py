from django.db.models import Count, Q
from rest_framework.response import Response
from rest_framework.views import APIView

from watchlists.models import Watchlist


class WatchlistStatsView(APIView):
    def get(self, request):
        counts = Watchlist.objects.filter(organization=request.user.organization).aggregate(
            total=Count("id"), archived=Count("id", filter=Q(archived=True))
        )
        return Response(counts)
