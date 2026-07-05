from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet


router = DefaultRouter()

router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

urlpatterns = router.urls
