import stripe.checkout
from rest_framework import status, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from payment.models import Payment
from payment.serializers import PaymentSerializer, CreatePaymentSerializer, PaymentResultSerializer, \
    PaymentRetrieveSerializer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()

    def get_queryset(self):
        user = self.request.user
        if self.action == "retrieve":
            queryset = Payment.objects.select_related().prefetch_related("borrowing__book")
        else:
            queryset = self.queryset
        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)
        return queryset

    def get_serializer_class(self):
        if self.action == "create_payment":
            return CreatePaymentSerializer
        if self.action in ["success", "cancel"]:
            return PaymentResultSerializer
        if self.action == "retrieve":
            return PaymentRetrieveSerializer
        return PaymentSerializer

    @action(detail=False, methods=["POST"], url_path="create_payment")
    def create_payment(self, request):
        serializer = CreatePaymentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                {"session_url": payment.session_url},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path="success", permission_classes=(permissions.AllowAny,))
    def success(self, request):
        session_id = request.query_params.get("session_id")
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            payment = Payment.objects.get(session_id=session_id)
            payment.status = Payment.Status.PAID
            payment.save()
            serializer = PaymentResultSerializer({"message": "Payment was successful"})
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = PaymentResultSerializer({"message": "Payment not completed"})
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"], url_path="cancel", permission_classes=(permissions.AllowAny,))
    def cancel(self, request):
        serializer = PaymentResultSerializer({"message": "Payment was cancelled"})
        return Response(serializer.data, status=status.HTTP_200_OK)
