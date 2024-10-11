from decimal import Decimal

import stripe
from rest_framework import serializers

from borrowing.models import Borrowing
from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        ]
        read_only_fields = [
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        ]


class CreatePaymentSerializer(serializers.Serializer):
    borrowing = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "request" in self.context:
            user = self.context["request"].user
            paid_borrowing_payments_ids = Payment.objects.filter(
                    type="PAYMENT", status="PAID"
                ).values_list("borrowing_id", flat=True)
            if user.is_staff:
                not_paid_borrowing_payments_ids = Borrowing.objects.exclude(
                    id__in=paid_borrowing_payments_ids
                )
            else:
                not_paid_borrowing_payments_ids = Borrowing.objects.exclude(
                    id__in=paid_borrowing_payments_ids
                ).filter(user=user)

            self.fields["borrowing"].queryset = not_paid_borrowing_payments_ids

    def validate(self, data):
        borrowing = data.get("borrowing")

        if Payment.objects.filter(borrowing=borrowing, type=Payment.Type.PAYMENT).exists():
            raise serializers.ValidationError("Payment already exist for this Borrowing")
        return data

    def create(self, validated_data):
        borrowing = validated_data["borrowing"]

        delta_days = (borrowing.expected_return_date - borrowing.borrow_date).days + 1
        amount = sum([book.daily_fee for book in borrowing.book.all()]) * Decimal(delta_days)

        books_in_borrowing = ", ".join([book.title for book in borrowing.book.all()])

        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Payment for {books_in_borrowing}",
                        },
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://127.0.0.1:8000/api/library/payments/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://127.0.0.1:8000/api/library/payments/cancel",
        )

        payment = Payment.objects.create(
            type=Payment.Type.PAYMENT,
            borrowing=borrowing,
            session_url=session.url,
            session_id=session.id,
            money_to_pay=amount,
        )
        return payment


class PaymentResultSerializer(serializers.Serializer):
    message = serializers.ReadOnlyField()
