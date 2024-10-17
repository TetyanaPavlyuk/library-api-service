import os

from django.contrib.auth import get_user_model
from django.db import models
from decimal import Decimal
from dotenv import load_dotenv
from rest_framework.exceptions import ValidationError

from book.models import Book


load_dotenv()


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ManyToManyField(Book, related_name="borrowing")
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="borrowings"
    )

    def calculate_payment_amount(self) -> Decimal:
        delta_days = (self.expected_return_date - self.borrow_date).days + 1
        amount = sum([book.daily_fee for book in self.book.all()]) * Decimal(delta_days)
        return amount

    def calculate_fine_amount(self) -> Decimal:
        if self.actual_return_date > self.expected_return_date:
            delta_days = (self.actual_return_date - self.expected_return_date).days
            amount = (
                sum([book.daily_fee for book in self.book.all()])
                * Decimal(delta_days)
                * Decimal(os.getenv("FINE_MULTIPLIER"))
            )
            return amount
        raise ValidationError("Borrowing is not overdue")

    @property
    def books_in_borrowing(self):
        return ", ".join([book.title for book in self.book.all()])

    def __str__(self):
        return f"Id: {self.id}. {self.user}: {[book.title for book in self.book.all()]}"

    class Meta:
        ordering = ["actual_return_date", "-borrow_date"]
