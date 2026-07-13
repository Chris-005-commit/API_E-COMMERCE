from rest_framework import serializers
from .models import Review
from apps.orders.models import Order


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

    def validate(self, attrs):
        user = self.context['request'].user
        product = attrs.get('product')
        rating = attrs.get('rating')

        if rating < 1 or rating > 5:
            raise serializers.ValidationError({"rating": "La calificación debe estar entre 1 y 5 estrellas."})

        has_purchased = Order.objects.filter(
            user=user,
            status='paid',
            items__product_variant__product=product
        ).exists()

        if not has_purchased:
            raise serializers.ValidationError({
                "product": "Solo puedes dejar una reseña en productos que hayas comprado y pagado."
            })

        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("Ya has dejado una reseña para este producto.")

        return attrs