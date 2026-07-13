from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Category, Product, ProductVariant
from apps.orders.models import Order
from apps.invoices.models import Invoice
from django.core.files.base import ContentFile


class InvoiceDownloadTestCase(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username='buyer6', password='Password123!', email='buyer6@example.com')
        self.other_user = User.objects.create_user(username='buyer7', password='Password123!', email='buyer7@example.com')
        
        # Create Order
        self.order = Order.objects.create(
            user=self.user,
            total_amount=100.00,
            status='paid'
        )

        # Create Invoice
        self.invoice = Invoice.objects.create(
            order=self.order,
            invoice_number='FAC-2026-TEST',
            total_amount=100.00
        )
        
        # Save a mock PDF file to the invoice model
        self.invoice.pdf_file.save(
            'factura_test.pdf',
            ContentFile(b'%PDF-1.4 Mock PDF Content')
        )

    def test_download_invoice_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/invoices/{self.invoice.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_download_invoice_non_owner_forbidden(self):
        # Other user should get 404 due to user scoping (get_queryset)
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/invoices/{self.invoice.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
