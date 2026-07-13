from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
import datetime

from .models import Coupon
from .serializers import CouponSerializer


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    @action(detail=False, methods=['get'], url_path='validate')
    def validate_coupon(self, request):
        code = request.query_params.get('code', None)
        if not code:
            return Response(
                {"detail": "Se requiere el código del cupón en los parámetros de consulta.", "valid": False},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response(
                {"detail": f"El cupón '{code}' no existe.", "valid": False},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if not coupon.active:
            return Response(
                {"detail": f"El cupón '{code}' no está activo.", "valid": False},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if coupon.expiration_date < datetime.date.today():
            return Response(
                {"detail": f"El cupón '{code}' ha expirado.", "valid": False},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            return Response(
                {"detail": f"El cupón '{code}' ha alcanzado su límite de usos.", "valid": False},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response({
            "valid": True,
            "code": coupon.code,
            "discount_percentage": coupon.discount_percentage,
            "min_purchase_amount": coupon.min_purchase_amount
        }, status=status.HTTP_200_OK)