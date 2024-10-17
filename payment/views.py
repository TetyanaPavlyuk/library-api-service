import asyncio
import stripe.checkout
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from payment.models import Payment
from payment.permissions import CanNotEditAndDeletePayments
from payment.serializers import (
    PaymentSerializer,
    CreatePaymentSerializer,
    PaymentResultSerializer,
    PaymentRetrieveSerializer,
    CreateFineSerializer,
)
from utils.telegram import send_telegram_message


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related("borrowing__user").prefetch_related(
        "borrowing__book"
    )
    permission_classes = [permissions.IsAuthenticated, CanNotEditAndDeletePayments]

    def get_queryset(self):
        user = self.request.user
        if not user.is_staff:
            return self.queryset.filter(borrowing__user=user)
        return self.queryset

    def get_serializer_class(self):
        if self.action == "create_payment":
            return CreatePaymentSerializer
        if self.action == "create_fine":
            return CreateFineSerializer
        if self.action in ["success", "cancel"]:
            return PaymentResultSerializer
        if self.action == "retrieve":
            return PaymentRetrieveSerializer
        return PaymentSerializer

    @action(detail=False, methods=["POST"], url_path="create_payment")
    def create_payment(self, request):
        serializer = CreatePaymentSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                {"session_url": payment.session_url},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["POST"], url_path="create_fine")
    def create_fine(self, request):
        serializer = CreateFineSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            fine = serializer.save()
            return Response(
                {"session_url": fine.session_url},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="success",
        permission_classes=(permissions.AllowAny,),
    )
    def success(self, request):
        session_id = request.query_params.get("session_id")
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            payment = Payment.objects.get(session_id=session_id)
            payment.status = Payment.Status.PAID
            payment.save()
            serializer = PaymentResultSerializer({"message": "Payment was successful"})

            message = (
                f"New payment was paid: \n"
                f"borrowing - {payment.borrowing}, \n"
                f"type - {payment.type}, \n"
                f"amount - {payment.money_to_pay}$."
            )
            asyncio.run(send_telegram_message(message))

            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = PaymentResultSerializer({"message": "Payment not completed"})
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["GET"],
        url_path="cancel",
        permission_classes=(permissions.AllowAny,),
    )
    def cancel(self, request):
        serializer = PaymentResultSerializer(
            {
                "message": "Payment was cancelled. It can be paid a bit later "
                "(session is available for only 24h.)"
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
