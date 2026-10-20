from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from watchlists.models import Watchlist
from watchlists.serializers import BulkArchiveSerializer


class WatchlistBulkArchiveView(APIView):
    def post(self, request):
        serializer = BulkArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        archived = Watchlist.objects.filter(
            organization=request.user.organization, id__in=serializer.validated_data["ids"]
        ).update(archived=True)
        return Response({"archived": archived}, status=status.HTTP_200_OK)
