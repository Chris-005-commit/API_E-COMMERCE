from django.db import models


class Coupon(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True
    )

    discount_percentage = models.PositiveIntegerField()

    active = models.BooleanField(
        default=True
    )

    expiration_date = models.DateField()

    def __str__(self):
        return self.code