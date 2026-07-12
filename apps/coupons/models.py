from django.db import models
from apps.products.models import Product, Category


class Coupon(models.Model):

    # Código del cupón
    code = models.CharField(
        max_length=50,
        unique=True
    )

    # Porcentaje de descuento
    discount_percentage = models.PositiveIntegerField()

    # Fecha de expiración
    expiration_date = models.DateField()

    # Estado del cupón
    active = models.BooleanField(
        default=True
    )

    # Compra mínima requerida para aplicar el cupón
    min_purchase_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Límite máximo de usos (None para usos ilimitados)
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    # Cantidad actual de veces que ha sido usado
    usage_count = models.PositiveIntegerField(
        default=0
    )

    # Productos elegibles (vacío significa que aplica a todos)
    valid_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='eligible_coupons'
    )

    # Categorías elegibles (vacío significa que aplica a todas)
    valid_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='eligible_coupons'
    )

    def __str__(self):
        return self.code