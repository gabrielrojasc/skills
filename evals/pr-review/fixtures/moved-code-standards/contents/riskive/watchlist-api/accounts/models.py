from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=200)


class User(AbstractUser):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
