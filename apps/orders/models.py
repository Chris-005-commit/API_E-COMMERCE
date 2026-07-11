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

    def save(self, *args, **kwargs):
        is_paid_transition = False
        if self.id:
            try:
                old_order = Order.objects.get(id=self.id)
                old_status = old_order.status
                new_status = self.status
                
                if new_status == 'paid' and old_status != 'paid':
                    is_paid_transition = True
                
                if new_status == 'cancelled' and old_status != 'cancelled':
                    for item in self.items.all():
                        variant = item.product_variant
                        variant.stock += item.quantity
                        variant.save()
                        
                        product = variant.product
                        product.stock += item.quantity
                        product.save()
                        
                elif old_status == 'cancelled' and new_status in ['pending', 'paid']:
                    for item in self.items.all():
                        variant = item.product_variant
                        if variant.stock < item.quantity:
                            raise ValueError(f"No hay suficiente stock para la variante '{variant}' y reactivar la orden.")
                            
                    for item in self.items.all():
                        variant = item.product_variant
                        variant.stock -= item.quantity
                        variant.save()
                        
                        product = variant.product
                        product.stock = max(0, product.stock - item.quantity)
                        product.save()
            except Order.DoesNotExist:
                pass
                
        super().save(*args, **kwargs)
        
        if is_paid_transition:
            from apps.invoices.models import Invoice
            from apps.invoices.services import generate_invoice_pdf
            import datetime
            
            try:
                invoice = self.invoice
            except Invoice.DoesNotExist:
                year = datetime.datetime.now().year
                invoice_number = f"FAC-{year}-{self.id:04d}"
                
                invoice = Invoice.objects.create(
                    order=self,
                    invoice_number=invoice_number,
                    total_amount=self.total_amount
                )
                generate_invoice_pdf(invoice)


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