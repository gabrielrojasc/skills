from django.db import models


class Watchlist(models.Model):
    organization = models.ForeignKey("accounts.Organization", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]


class WatchlistMember(models.Model):
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name="members")
    name = models.CharField(max_length=200)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
