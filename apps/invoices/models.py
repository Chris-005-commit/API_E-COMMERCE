from django.db import models
from apps.orders.models import Order


class Invoice(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invoice'
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True
    )

    issued_at = models.DateTimeField(
        auto_now_add=True
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    pdf_file = models.FileField(
        upload_to='invoices/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Factura {self.invoice_number}"