from django.db import models


class PhishingAlert(models.Model):
    enterprise = models.ForeignKey("enterprises.Enterprise", on_delete=models.CASCADE)
    domain = models.CharField(max_length=253)
    impersonated_brand = models.CharField(max_length=200)
    detected_at = models.DateTimeField()
    takedown_status = models.CharField(max_length=32, default="open")
