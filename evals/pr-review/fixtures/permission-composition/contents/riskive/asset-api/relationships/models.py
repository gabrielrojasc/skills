from django.db import models


class RelationshipType(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Relationship(models.Model):
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE)
    parent = models.ForeignKey("assets.Asset", on_delete=models.CASCADE, related_name="child_links")
    child = models.ForeignKey("assets.Asset", on_delete=models.CASCADE, related_name="parent_links")
    type = models.ForeignKey(RelationshipType, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "parent", "child"], name="unique_relationship")]
