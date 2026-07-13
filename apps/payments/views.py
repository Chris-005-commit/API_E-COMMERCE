from rest_framework import viewsets

from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Payment.objects.all()
            return Payment.objects.filter(order__user=user)
        return Payment.objects.none()