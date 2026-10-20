from django.db import models


class Subscription(models.Model):
    url = models.URLField()
    active = models.BooleanField(default=False)
