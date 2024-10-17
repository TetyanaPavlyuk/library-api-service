from django.db import models
from django.utils.translation import gettext_lazy as _

from borrowing.models import Borrowing


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PAID = "PAID", _("Paid")

    class Type(models.TextChoices):
        PAYMENT = "PAYMENT", _("Payment")
        FINE = "FINE", _("Fine")

    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.PENDING
    )
    type = models.CharField(max_length=8, choices=Type.choices, default=Type.PAYMENT)
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(blank=True, max_length=511)
    session_id = models.CharField(max_length=511, blank=True, null=True)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["type", "borrowing"], name="unique_payment"
            ),
        ]

    def __str__(self):
        return f"{self.type} ({self.borrowing.user.full_name}): {self.status}"

    def save(self, *args, **kwargs):
        if self.money_to_pay <= 0 and self.status == self.Status.PAID:
            raise ValueError("Cannot be 'Paid' if money_to_pay is zero or negative")
        super().save(*args, **kwargs)
