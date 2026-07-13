from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from apps.cart.models import Cart
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

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        user = request.user
        
        # 1. Obtener o crear el carrito del usuario
        cart, created = Cart.objects.get_or_create(user=user)
            
        # 2. Verificar si el carrito tiene ítems
        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response(
                {"detail": "El carrito está vacío. Agrega productos antes de realizar el checkout."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 3. Preparar la estructura de datos para el serializador
        items_data = []
        for item in cart_items:
            items_data.append({
                'product_variant': item.product_variant.id,
                'quantity': item.quantity
            })
            
        coupon_code = request.data.get('coupon_code', None)
        
        payload = {
            'items': items_data
        }
        if coupon_code:
            payload['coupon'] = coupon_code
            
        # 4. Inicializar y validar con el serializador
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        
        # 5. Ejecutar la creación de la orden y vaciado de carrito atómicamente
        with transaction.atomic():
            order = serializer.save(user=user)
            cart_items.delete()
            
        # 6. Retornar la orden serializada
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return OrderItem.objects.all()
            return OrderItem.objects.filter(order__user=user)
        return OrderItem.objects.none()
