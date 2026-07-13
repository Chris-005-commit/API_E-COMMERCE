import datetime
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from apps.coupons.models import Coupon


class CouponValidationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer5', password='Password123!', email='buyer5@example.com')
        
        # Valid coupon
        self.valid_coupon = Coupon.objects.create(
            code='VALID50',
            discount_percentage=50,
            expiration_date=datetime.date.today() + datetime.timedelta(days=5),
            active=True
        )

        # Expired coupon
        self.expired_coupon = Coupon.objects.create(
            code='OLD50',
            discount_percentage=50,
            expiration_date=datetime.date.today() - datetime.timedelta(days=5),
            active=True
        )

        # Inactive coupon
        self.inactive_coupon = Coupon.objects.create(
            code='INACTIVE',
            discount_percentage=20,
            expiration_date=datetime.date.today() + datetime.timedelta(days=5),
            active=False
        )

    def test_validate_coupon_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/coupons/validate/?code={self.valid_coupon.code}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['discount_percentage'], 50)

    def test_validate_coupon_expired(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/coupons/validate/?code={self.expired_coupon.code}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])

    def test_validate_coupon_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/coupons/validate/?code={self.inactive_coupon.code}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])

    def test_validate_coupon_nonexistent(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/coupons/validate/?code=NO_CUPON')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['valid'])
