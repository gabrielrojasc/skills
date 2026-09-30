from django.db import models


class Subscription(models.Model):
    url = models.URLField()
    active = models.BooleanField(default=True)


class Delivery(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status_code = models.IntegerField()
