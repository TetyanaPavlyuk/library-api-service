from rest_framework.viewsets import ModelViewSet

from payment.models import Payment
from payment.serializers import PaymentSerializer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
