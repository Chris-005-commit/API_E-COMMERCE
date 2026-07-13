from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Category, Product, ProductVariant
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.invoices.models import Invoice


class PaymentIntegrationTestCase(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='buyer2', password='Password123!', email='buyer2@example.com')
        
        # Create category, product, variant
        self.category = Category.objects.create(name='Electronics', slug='elec')
        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            description='Core i7 Laptop',
            price=1200.00,
            stock=10
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='16GB',
            color='Silver',
            stock=5
        )

        # Create Order
        self.order = Order.objects.create(
            user=self.user,
            total_amount=1200.00,
            status='pending'
        )
        
        # Create Payment
        self.payment = Payment.objects.create(
            order=self.order,
            amount=1200.00,
            payment_method='mercadopago',
            status='pending'
        )

    def test_get_payment_url(self):
        self.client.force_authenticate(user=self.user)
        
        # Call the viewset 'pay' action
        response = self.client.post(f'/api/payments/{self.payment.id}/pay/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("payment_url", response.data)
        # Should contain simulate endpoint since token is not set
        self.assertIn(f"/api/payments/simulate/{self.payment.id}/", response.data['payment_url'])

    def test_webhook_payment_approved(self):
        # Trigger webhook simulation
        payload = {
            "payment_id": self.payment.id,
            "status": "approved"
        }
        
        # Webhook should be accessible by anyone (AllowAny)
        response = self.client.post('/api/payments/webhook/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment is approved
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'approved')
        
        # Verify order transitions to paid
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        
        # Verify invoice is automatically created
        self.assertEqual(Invoice.objects.filter(order=self.order).count(), 1)
        invoice = Invoice.objects.get(order=self.order)
        self.assertEqual(invoice.total_amount, 1200.00)
        self.assertTrue(invoice.pdf_file)  # ReportLab generated PDF should be present!

    def test_webhook_payment_cancelled(self):
        # Trigger webhook cancellation
        payload = {
            "payment_id": self.payment.id,
            "status": "cancelled"
        }
        
        response = self.client.post('/api/payments/webhook/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify payment is cancelled
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'cancelled')
        
        # Verify order is cancelled
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
