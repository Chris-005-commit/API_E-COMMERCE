import datetime
from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from apps.products.models import ProductVariant
from apps.coupons.models import Coupon


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product_variant', 'quantity', 'unit_price']
        extra_kwargs = {
            'order': {'read_only': True},
            'unit_price': {'read_only': True}
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    coupon = serializers.SlugRelatedField(
        slug_field='code',
        queryset=Coupon.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'status', 'created_at', 'coupon', 'items']
        extra_kwargs = {
            'total_amount': {'read_only': True},
            'user': {'required': False, 'allow_null': True}
        }

    def validate(self, attrs):
        is_create = self.instance is None
        items_data = attrs.get('items', None)

        if is_create and items_data is None:
            raise serializers.ValidationError({"items": "Una orden debe contener al menos un ítem."})
        
        coupon = attrs.get('coupon', None)
        if coupon is not None:
            if not coupon.active:
                raise serializers.ValidationError({"coupon": f"El cupón '{coupon.code}' no está activo."})
            
            if coupon.expiration_date < datetime.date.today():
                raise serializers.ValidationError({"coupon": f"El cupón '{coupon.code}' ha expirado."})
            
            if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
                raise serializers.ValidationError({"coupon": f"El cupón '{coupon.code}' ha alcanzado su límite de usos."})
        
        if items_data is not None:
            if not items_data:
                raise serializers.ValidationError({"items": "Una orden debe contener al menos un ítem."})
            
            variant_quantities = {}
            subtotal_bruto = 0
            has_eligible_item = False
            
            for item_data in items_data:
                variant = item_data.get('product_variant')
                quantity = item_data.get('quantity', 1)
                
                if quantity <= 0:
                    raise serializers.ValidationError({"items": "La cantidad de cada ítem debe ser mayor a cero."})
                    
                if variant in variant_quantities:
                    variant_quantities[variant] += quantity
                else:
                    variant_quantities[variant] = quantity
                    
                subtotal_bruto += variant.product.price * quantity
                
                if coupon:
                    is_item_eligible = True
                    if coupon.valid_products.exists() and variant.product not in coupon.valid_products.all():
                        is_item_eligible = False
                    if coupon.valid_categories.exists() and variant.product.category not in coupon.valid_categories.all():
                        is_item_eligible = False
                    
                    if is_item_eligible:
                        has_eligible_item = True

            if coupon and coupon.min_purchase_amount is not None:
                if subtotal_bruto < coupon.min_purchase_amount:
                    raise serializers.ValidationError({
                        "coupon": f"El cupón '{coupon.code}' requiere una compra mínima de ${coupon.min_purchase_amount:.2f} (subtotal actual: ${subtotal_bruto:.2f})."
                    })
            
            if coupon and (coupon.valid_products.exists() or coupon.valid_categories.exists()):
                if not has_eligible_item:
                    raise serializers.ValidationError({
                        "coupon": f"El cupón '{coupon.code}' no es aplicable a ninguno de los productos en tu carrito."
                    })

            for variant, total_requested in variant_quantities.items():
                if variant.stock < total_requested:
                    raise serializers.ValidationError(
                        f"No hay suficiente stock para la variante '{variant}' "
                        f"(disponible: {variant.stock}, solicitado: {total_requested})."
                    )
                
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        coupon = validated_data.get('coupon', None)
        
        user = validated_data.get('user')
        if not user and 'request' in self.context:
            request_user = self.context['request'].user
            if request_user and request_user.is_authenticated:
                user = request_user
                
        if not user:
            raise serializers.ValidationError(
                {"user": "Se requiere un usuario para crear la orden."}
            )

        with transaction.atomic():
            if coupon:
                # Bloqueo de concurrencia
                coupon = Coupon.objects.select_for_update().get(id=coupon.id)
                if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
                    raise serializers.ValidationError({
                        "coupon": f"El cupón '{coupon.code}' ha alcanzado su límite de usos."
                    })
                coupon.usage_count += 1
                coupon.save()

            order = Order.objects.create(
                user=user,
                total_amount=0,
                status=validated_data.get('status', 'pending'),
                coupon=coupon
            )
            
            for item_data in items_data:
                variant = item_data.get('product_variant')
                quantity = item_data.get('quantity')
                unit_price = variant.product.price
                
                OrderItem.objects.create(
                    order=order,
                    product_variant=variant,
                    quantity=quantity,
                    unit_price=unit_price
                )
                
                variant.stock -= quantity
                variant.save()
                
                product = variant.product
                product.stock = max(0, product.stock - quantity)
                product.save()
                
            # Calcular el total real centralizado
            order.calculate_total()
            
        return order

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except ValueError as e:
            raise serializers.ValidationError({"status": str(e)})
