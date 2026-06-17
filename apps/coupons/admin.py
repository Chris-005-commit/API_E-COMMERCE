from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'code',
        'discount_percentage',
        'expiration_date',
        'active'
    )

    list_filter = (
        'active',
    )

    search_fields = (
        'code',
    )