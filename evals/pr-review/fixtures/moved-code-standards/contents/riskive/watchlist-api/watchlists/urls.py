from django.urls import path
from rest_framework.routers import DefaultRouter

from watchlists.views import (
    WatchlistBulkArchiveView,
    WatchlistExportView,
    WatchlistMemberViewSet,
    WatchlistStatsView,
    WatchlistViewSet,
)

router = DefaultRouter()
router.register("watchlists", WatchlistViewSet, basename="watchlist")
router.register("watchlist-members", WatchlistMemberViewSet, basename="watchlist-member")

urlpatterns = [
    path("watchlists/export/", WatchlistExportView.as_view(), name="watchlist-export"),
    path("watchlists/bulk-archive/", WatchlistBulkArchiveView.as_view(), name="watchlist-bulk-archive"),
    path("watchlists/stats/", WatchlistStatsView.as_view(), name="watchlist-stats"),
    *router.urls,
]
