from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Category, Product, ProductVariant
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review


class ReviewValidationTestCase(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username='buyer3', password='Password123!', email='buyer3@example.com')
        self.other_user = User.objects.create_user(username='buyer4', password='Password123!', email='buyer4@example.com')
        
        # Create product info
        self.category = Category.objects.create(name='Books', slug='books')
        self.product = Product.objects.create(
            category=self.category,
            name='Django Book',
            description='Django Rest Framework Book',
            price=15.00,
            stock=100
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='Digital',
            color='Ebook',
            stock=100
        )

    def test_anonymous_user_cannot_review(self):
        payload = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Amazing book!'
        }
        response = self.client.post('/api/reviews/', payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unpurchased_product_review_rejected(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Good product.'
        }
        response = self.client.post('/api/reviews/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Solo puedes dejar una reseña en productos que hayas comprado y pagado.", response.data['product'])

    def test_invalid_rating_rejected(self):
        self.client.force_authenticate(user=self.user)
        
        # Create a paid order for the user
        order = Order.objects.create(user=self.user, total_amount=15.00, status='paid')
        OrderItem.objects.create(order=order, product_variant=self.variant, quantity=1, unit_price=15.00)
        
        # Rating = 6 should be rejected
        payload = {
            'product': self.product.id,
            'rating': 6,
            'comment': 'Exceptional!'
        }
        response = self.client.post('/api/reviews/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("La calificación debe estar entre 1 y 5 estrellas.", response.data['rating'])

    def test_verified_purchase_review_success_and_prevent_duplicates(self):
        self.client.force_authenticate(user=self.user)
        
        # Create a paid order for the user
        order = Order.objects.create(user=self.user, total_amount=15.00, status='paid')
        OrderItem.objects.create(order=order, product_variant=self.variant, quantity=1, unit_price=15.00)
        
        # Post review should succeed
        payload = {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Great read!'
        }
        response = self.client.post('/api/reviews/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
        
        # Attempting duplicate review should fail
        response_duplicate = self.client.post('/api/reviews/', payload)
        self.assertEqual(response_duplicate.status_code, status.HTTP_400_BAD_REQUEST)
