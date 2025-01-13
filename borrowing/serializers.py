from django.db import transaction
from rest_framework import serializers

from book.models import Book
from book.serializers import BookSerializer
from borrowing.models import Borrowing
from payment.serializers import PaymentSlimSerializer
from user.serializers import UserShortSerializer


class BorrowingAdminSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Book.objects.all(), required=True
    )

    class Meta:
        model = Borrowing
        fields = ["id", "user", "book", "expected_return_date"]

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
                    raise serializers.ValidationError(
                        f"Book {book.title} isn't available for borrowing today."
                    )

            borrowing.save()

            return borrowing


class BorrowingUserSerializer(BorrowingAdminSerializer):
    class Meta:
        model = Borrowing
        fields = ["id", "book", "expected_return_date"]


class BorrowingListAdminSerializer(serializers.ModelSerializer):
    book = serializers.SlugRelatedField(
        slug_field="title",
        many=True,
        queryset=Book.objects.all(),
    )
    user = UserShortSerializer()
    payment = PaymentSlimSerializer(many=True, source="payments")

    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "payment",
        ]


class BorrowingListUserSerializer(BorrowingListAdminSerializer):
    class Meta:
        model = Borrowing
        fields = [
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "payment",
        ]


class BorrowingRetrieveSerializer(BorrowingListAdminSerializer):
    book = BookSerializer(many=True, read_only=True)
