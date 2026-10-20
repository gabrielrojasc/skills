import csv

from django.http import HttpResponse
from rest_framework.views import APIView

from watchlists.models import Watchlist


class WatchlistExportView(APIView):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="watchlists.csv"'
        writer = csv.writer(response)
        writer.writerow(["id", "name", "archived"])
        for watchlist in Watchlist.objects.filter(organization=request.user.organization):
            writer.writerow([watchlist.id, watchlist.name, watchlist.archived])
        return response
