from django.contrib.auth import get_user_model
from django.db import models

from book.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ManyToManyField(Book, related_name="borrowing")
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="borrowings"
    )

    def __str__(self):
        return f"{self.user}: {[book.title for book in self.book.all()]}"

    class Meta:
        ordering = ["actual_return_date", "-borrow_date"]
