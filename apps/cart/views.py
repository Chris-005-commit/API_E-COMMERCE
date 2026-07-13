from rest_framework import viewsets


from .models import Cart, CartItem


from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer

    def get_queryset(self):
        # Aseguramos que el usuario tenga un carrito creado antes de listar
        if self.request.user.is_authenticated:
            Cart.objects.get_or_create(user=self.request.user)
            return Cart.objects.filter(user=self.request.user)
        return Cart.objects.none()


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CartItem.objects.filter(cart__user=self.request.user)
        return CartItem.objects.none()

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)

