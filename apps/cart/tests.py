from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Category, Product, ProductVariant
from apps.cart.models import Cart, CartItem


class CartScopingTestCase(APITestCase):
    def setUp(self):
        # Create users
        self.user_a = User.objects.create_user(username='user_a', password='Password123!', email='a@example.com')
        self.user_b = User.objects.create_user(username='user_b', password='Password123!', email='b@example.com')

        # Create category, product, variant
        self.category = Category.objects.create(name='Clothing', slug='clothing')
        self.product = Product.objects.create(
            category=self.category,
            name='T-Shirt',
            description='A nice t-shirt',
            price=20.00,
            stock=100
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            size='M',
            color='Blue',
            stock=50
        )

    def test_cart_auto_creation_and_scoping(self):
        # Authenticate as user_a
        self.client.force_authenticate(user=self.user_a)
        
        # Verify cart list returns user_a's cart
        response = self.client.get('/api/carts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain exactly 1 cart (auto-created)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user_a.id)

        # Authenticate as user_b
        self.client.force_authenticate(user=self.user_b)
        response_b = self.client.get('/api/carts/')
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_b.data), 1)
        self.assertEqual(response_b.data[0]['user'], self.user_b.id)
        # Verify it's a different cart
        self.assertNotEqual(response.data[0]['id'], response_b.data[0]['id'])

    def test_cart_item_scoping(self):
        # Create user_a cart item
        cart_a, _ = Cart.objects.get_or_create(user=self.user_a)
        cart_item_a = CartItem.objects.create(cart=cart_a, product_variant=self.variant, quantity=2)

        # Authenticate as user_b (who has no cart items)
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get('/api/cart-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Cannot see user_a's cart items

        # Attempt to access user_a's cart item directly
        response_detail = self.client.get(f'/api/cart-items/{cart_item_a.id}/')
        self.assertEqual(response_detail.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to update user_a's cart item
        response_update = self.client.put(f'/api/cart-items/{cart_item_a.id}/', {'quantity': 5})
        self.assertEqual(response_update.status_code, status.HTTP_404_NOT_FOUND)

        # Attempt to delete user_a's cart item
        response_delete = self.client.delete(f'/api/cart-items/{cart_item_a.id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_404_NOT_FOUND)

        # Authenticate as user_a
        self.client.force_authenticate(user=self.user_a)
        response_a = self.client.get('/api/cart-items/')
        self.assertEqual(len(response_a.data), 1)
        self.assertEqual(response_a.data[0]['id'], cart_item_a.id)

    def test_post_cart_item_auto_associates_with_user_cart(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Post to cart-items without specifying cart (since it is read-only)
        payload = {
            'product_variant': self.variant.id,
            'quantity': 3
        }
        response = self.client.post('/api/cart-items/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify it was added to user_a's cart
        cart_a = Cart.objects.get(user=self.user_a)
        self.assertEqual(response.data['cart'], cart_a.id)
        self.assertEqual(response.data['quantity'], 3)
