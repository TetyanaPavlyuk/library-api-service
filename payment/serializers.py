from django.db.models import Q, F
from rest_framework import serializers

from utils.stripe import (
    create_stripe_session_for_payment,
    create_stripe_session_for_fine,
)
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
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        ]


class CreatePaymentSerializer(serializers.Serializer):
    borrowing = serializers.PrimaryKeyRelatedField(queryset=Borrowing.objects.all())

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

            self.fields[
                "borrowing"
            ].queryset = not_paid_borrowing_payments_ids.select_related().prefetch_related(
                "book"
            )

    def validate(self, data):
        borrowing = data.get("borrowing")

        if Payment.objects.filter(
            borrowing=borrowing, type=Payment.Type.PAYMENT
        ).exists():
            raise serializers.ValidationError(
                "Payment already exist for this Borrowing"
            )
        return data

    def create(self, validated_data):
        borrowing = validated_data["borrowing"]

        session = create_stripe_session_for_payment(borrowing)

        payment = Payment.objects.create(
            type=Payment.Type.PAYMENT,
            borrowing=borrowing,
            session_url=session.url,
            session_id=session.id,
            money_to_pay=borrowing.calculate_payment_amount(),
        )
        return payment


class CreateFineSerializer(serializers.Serializer):
    borrowing = serializers.PrimaryKeyRelatedField(queryset=Borrowing.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "request" in self.context:
            user = self.context["request"].user
            borrowing_overdue = Borrowing.objects.filter(
                Q(actual_return_date__isnull=False)
                & Q(expected_return_date__lt=F("actual_return_date"))
            )
            paid_borrowing_fine_ids = Payment.objects.filter(
                type="FINE", status="PAID"
            ).values_list("borrowing_id", flat=True)
            if user.is_staff:
                not_paid_borrowing_fine_ids = borrowing_overdue.exclude(
                    id__in=paid_borrowing_fine_ids
                )
            else:
                not_paid_borrowing_fine_ids = borrowing_overdue.exclude(
                    id__in=paid_borrowing_fine_ids
                ).filter(user=user)

            self.fields[
                "borrowing"
            ].queryset = not_paid_borrowing_fine_ids.select_related().prefetch_related(
                "book"
            )

    def validate(self, data):
        borrowing = data.get("borrowing")

        if Payment.objects.filter(borrowing=borrowing, type=Payment.Type.FINE).exists():
            raise serializers.ValidationError("Fine already exist for this Borrowing")
        return data

    def create(self, validated_data):
        borrowing = validated_data["borrowing"]

        session = create_stripe_session_for_fine(borrowing)

        fine = Payment.objects.create(
            type=Payment.Type.FINE,
            borrowing=borrowing,
            session_url=session.url,
            session_id=session.id,
            money_to_pay=borrowing.calculate_fine_amount(),
        )
        return fine


class PaymentResultSerializer(serializers.Serializer):
    message = serializers.ReadOnlyField()


class PaymentRetrieveSerializer(PaymentSerializer):
    borrowing_user = serializers.CharField(source="borrowing.user")
    borrowing_books = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source="borrowing.book",
        slug_field="title",
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "borrowing_user",
            "borrowing_books",
            "session_url",
            "session_id",
            "money_to_pay",
        ]


class PaymentSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "status", "type", "money_to_pay"]
