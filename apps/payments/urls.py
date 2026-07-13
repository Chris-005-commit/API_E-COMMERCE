from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, payment_simulation_view

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = router.urls + [
    path('payments/simulate/<int:payment_id>/', payment_simulation_view, name='payment-simulation'),
]