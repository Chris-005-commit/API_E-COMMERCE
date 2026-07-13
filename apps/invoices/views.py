from rest_framework import viewsets

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Invoice.objects.all()
            return Invoice.objects.filter(order__user=user)
        return Invoice.objects.none()