from django.db import models
from django.contrib.auth.models import User

# Importa las variantes de productos
from apps.products.models import ProductVariant


class Cart(models.Model):
    # Usuario propietario del carrito
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    # Fecha de creación
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Carrito de {self.user.username}"


class CartItem(models.Model):
    # Carrito asociado
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # Variante seleccionada
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE
    )

    # Cantidad agregada
    quantity = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return f"{self.product_variant} x {self.quantity}"