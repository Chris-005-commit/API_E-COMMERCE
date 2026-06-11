from django.db import models
from django.contrib.auth.models import User
from apps.products.models import ProductVariant


class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):

    # Orden a la que pertenece
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Producto comprado
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE
    )

    # Cantidad comprada
    quantity = models.PositiveIntegerField(
        default=1
    )

    # Precio unitario al momento de la compra
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.product_variant} x {self.quantity}"