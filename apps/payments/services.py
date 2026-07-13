from decouple import config
import urllib.request
import urllib.parse
import json

def create_payment_preference(payment, request=None):
    """
    Genera un enlace de pago (init_point) llamando a la API de Mercado Pago
    si el token MERCADOPAGO_ACCESS_TOKEN está configurado.
    De lo contrario, retorna un enlace local para simular el pago.
    """
    access_token = config('MERCADOPAGO_ACCESS_TOKEN', default=None)
    
    if access_token:
        try:
            url = "https://api.mercadopago.com/checkout/preferences"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            order = payment.order
            items = []
            
            # Agregar los artículos de la orden
            for item in order.items.all():
                variant = item.product_variant
                items.append({
                    "title": f"{variant.product.name} ({variant.size} - {variant.color})",
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "currency_id": "USD"
                })
            
            # Manejar el descuento del cupón
            subtotal_bruto = sum(item.unit_price * item.quantity for item in order.items.all())
            discount_amount = float(subtotal_bruto - order.total_amount)
            if discount_amount > 0:
                items.append({
                    "title": "Descuento por Cupón",
                    "quantity": 1,
                    "unit_price": -discount_amount,
                    "currency_id": "USD"
                })
            
            # Resolver la URL del webhook
            domain = "https://yourdomain.com"
            if request:
                domain = request.build_absolute_uri('/')[:-1]
                
            webhook_url = f"{domain}/api/payments/webhook/"
            
            payload = {
                "items": items,
                "back_urls": {
                    "success": f"{domain}/api/payments/success/",
                    "failure": f"{domain}/api/payments/failure/",
                    "pending": f"{domain}/api/payments/pending/"
                },
                "auto_return": "approved",
                "notification_url": webhook_url,
                "external_reference": str(payment.id)
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data.get('init_point')
                
        except Exception as e:
            print(f"Error calling Mercado Pago API: {e}")
            
    # Simulación local
    domain = "http://127.0.0.1:8000"
    if request:
        domain = request.build_absolute_uri('/')[:-1]
    return f"{domain}/api/payments/simulate/{payment.id}/"
