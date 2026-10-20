from django.db import models


class Alert(models.Model):
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default="new")
