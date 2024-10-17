from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = "HR", _("Hard")
        SOFT = "SF", _("Soft")

    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    cover = models.CharField(max_length=8, choices=Cover, null=True, blank=True)
    inventory = models.IntegerField(default=1)
    daily_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.title} - {self.author} ({self.inventory})"

    class Meta:
        ordering = ["title"]
        constraints = [
            models.CheckConstraint(
                condition=Q(inventory__gte=0),
                name="inventory_gte_0"
            )
        ]
