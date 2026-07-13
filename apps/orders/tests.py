import datetime
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Category, Product, ProductVariant
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order
from apps.coupons.models import Coupon


class CheckoutTestCase(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username='buyer', password='Password123!', email='buyer@example.com')
        
        # Create categories and products
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Smartphone',
            description='Latest flagship smartphone',
            price=500.00,
            stock=100
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='128GB',
            color='Black',
            stock=10
        )

        # Create a valid coupon
        self.coupon = Coupon.objects.create(
            code='SAVE10',
            discount_percentage=10,
            expiration_date=datetime.date.today() + datetime.timedelta(days=7),
            active=True
        )

    def test_checkout_empty_cart(self):
        self.client.force_authenticate(user=self.user)
        
        # Post to checkout endpoint with empty cart
        response = self.client.post('/api/orders/checkout/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("El carrito está vacío", response.data['detail'])

    def test_checkout_success(self):
        # Create cart item
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product_variant=self.variant, quantity=2)

        self.client.force_authenticate(user=self.user)

        # Checkout
        response = self.client.post('/api/orders/checkout/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, 1000.00)  # 500 * 2
        
        # Check stock deduction
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 8)  # 10 - 2
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 98)  # 100 - 2
        
        # Check cart was cleared
        self.assertEqual(cart.items.count(), 0)

    def test_checkout_insufficient_stock(self):
        # Create cart item with quantity greater than stock
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product_variant=self.variant, quantity=12)

        self.client.force_authenticate(user=self.user)

        # Checkout
        response = self.client.post('/api/orders/checkout/')
        # Validation error returns 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check no order was created
        self.assertEqual(Order.objects.count(), 0)
        
        # Check stock was not deducted
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 10)
        
        # Check cart item still exists
        self.assertEqual(cart.items.count(), 1)

    def test_checkout_with_coupon(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product_variant=self.variant, quantity=2)

        self.client.force_authenticate(user=self.user)

        # Checkout with coupon
        payload = {'coupon_code': 'SAVE10'}
        response = self.client.post('/api/orders/checkout/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check total amount has 10% discount applied: 1000.00 - 10% = 900.00
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.total_amount, 900.00)
