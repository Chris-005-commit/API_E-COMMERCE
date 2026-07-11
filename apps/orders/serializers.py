from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem
from apps.products.models import ProductVariant


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

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'status', 'created_at', 'items']
        extra_kwargs = {
            'total_amount': {'read_only': True},
            'user': {'required': False, 'allow_null': True}
        }

    def validate(self, attrs):
        is_create = self.instance is None
        items_data = attrs.get('items', None)

        if is_create and items_data is None:
            raise serializers.ValidationError({"items": "Una orden debe contener al menos un ítem."})
        
        if items_data is not None:
            if not items_data:
                raise serializers.ValidationError({"items": "Una orden debe contener al menos un ítem."})
            
            variant_quantities = {}
            for item_data in items_data:
                variant = item_data.get('product_variant')
                quantity = item_data.get('quantity', 1)
                
                if quantity <= 0:
                    raise serializers.ValidationError({"items": "La cantidad de cada ítem debe ser mayor a cero."})
                    
                if variant in variant_quantities:
                    variant_quantities[variant] += quantity
                else:
                    variant_quantities[variant] = quantity

            for variant, total_requested in variant_quantities.items():
                if variant.stock < total_requested:
                    raise serializers.ValidationError(
                        f"No hay suficiente stock para la variante '{variant}' "
                        f"(disponible: {variant.stock}, solicitado: {total_requested})."
                    )
                
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
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
            order = Order.objects.create(
                user=user,
                total_amount=0,
                status=validated_data.get('status', 'pending')
            )
            
            total_amount = 0
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
                
                total_amount += unit_price * quantity
                
            order.total_amount = total_amount
            order.save()
            
        return order

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except ValueError as e:
            raise serializers.ValidationError({"status": str(e)})