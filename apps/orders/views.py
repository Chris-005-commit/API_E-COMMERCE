from rest_framework import viewsets
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Order.objects.all()
            return Order.objects.filter(user=user)
        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return OrderItem.objects.all()
            return OrderItem.objects.filter(order__user=user)
        return OrderItem.objects.none()