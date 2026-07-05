from django.db import models


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

    def __str__(self):
        return self.code