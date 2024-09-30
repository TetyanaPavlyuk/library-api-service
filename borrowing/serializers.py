from django.db import transaction
from rest_framework import serializers

from book.models import Book
from book.serializers import BookSerializer
from borrowing.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Book.objects.all(),
        required=True
    )

    class Meta:
        model = Borrowing
        fields = ["id", "expected_return_date", "actual_return_date", "book"]

    def create(self, validated_data):
        with transaction.atomic():
            books_data = validated_data.pop("book")
            borrowing = Borrowing.objects.create(**validated_data)

            for book in books_data:
                if book.inventory > 0:
                    borrowing.book.add(book.id)
                    book.inventory -= 1
                    book.save()

                else:
                    raise serializers.ValidationError(f"Book {book.title} isn't available for borrowing")
            return borrowing


class BorrowingListSerializer(serializers.ModelSerializer):
    book = BookSerializer(many=True, read_only=True)

    class Meta:
        model = Borrowing
        fields = ["id", "borrow_date", "expected_return_date", "actual_return_date", "book"]
