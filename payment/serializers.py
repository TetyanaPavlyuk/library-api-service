from  rest_framework import serializers

from borrowing.serializers import BorrowingListAdminSerializer
from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingListAdminSerializer(read_only=True)
    class Meta:
        model = Payment
        fields = [
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay"
        ]
