from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import HttpResponse, Http404
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import Payment
from .serializers import PaymentSerializer
from .services import create_payment_preference


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Payment.objects.all()
            return Payment.objects.filter(order__user=user)
        return Payment.objects.none()

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        payment = self.get_object()
        
        # Generar enlace Mercado Pago o Enlace de Simulación
        init_point = create_payment_preference(payment, request=request)
        return Response({"payment_url": init_point}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='webhook', permission_classes=[AllowAny])
    def webhook(self, request):
        payment_id = request.data.get('payment_id', None)
        status_str = request.data.get('status', 'approved')
        
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.status = status_str
                payment.save()
                return Response(
                    {"detail": f"Pago #{payment_id} actualizado a {status_str}."},
                    status=status.HTTP_200_OK
                )
            except Payment.DoesNotExist:
                return Response(
                    {"detail": f"Pago #{payment_id} no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response({"detail": "Notificación recibida sin ID de pago."}, status=status.HTTP_400_BAD_REQUEST)


@xframe_options_exempt
def payment_simulation_view(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        raise Http404("Pago no encontrado")
        
    order = payment.order
    items_html = ""
    for item in order.items.all():
        variant = item.product_variant
        items_html += f"""
        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px;">
            <span style="color: #94A3B8;">{variant.product.name} ({variant.size} - {variant.color}) x{item.quantity}</span>
            <span style="font-weight: 600; color: #F8FAFC;">${(item.unit_price * item.quantity):.2f}</span>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simulador de Pago - Mercado Pago</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {{
                box-sizing: border-box;
                font-family: 'Outfit', sans-serif;
                margin: 0;
                padding: 0;
            }}
            body {{
                background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                color: #F8FAFC;
            }}
            .card {{
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
                width: 100%;
                max-width: 480px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                text-align: center;
            }}
            .logo {{
                font-weight: 700;
                font-size: 22px;
                color: #38BDF8;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }}
            .title {{
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 8px;
                color: #FFFFFF;
            }}
            .subtitle {{
                font-size: 14px;
                color: #94A3B8;
                margin-bottom: 30px;
            }}
            .order-summary {{
                background: rgba(15, 23, 42, 0.4);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 32px;
                text-align: left;
                border: 1px solid rgba(255, 255, 255, 0.04);
            }}
            .summary-title {{
                font-size: 12px;
                font-weight: 600;
                color: #38BDF8;
                text-transform: uppercase;
                margin-bottom: 12px;
                letter-spacing: 0.05em;
            }}
            .total-row {{
                display: flex;
                justify-content: space-between;
                padding-top: 15px;
                margin-top: 10px;
                border-top: 2px dashed rgba(255, 255, 255, 0.1);
                font-size: 18px;
                font-weight: 700;
            }}
            .btn-group {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            .btn {{
                width: 100%;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                border: none;
                outline: none;
            }}
            .btn-approve {{
                background: linear-gradient(90deg, #10B981 0%, #059669 100%);
                color: #FFFFFF;
                box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
            }}
            .btn-approve:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
            }}
            .btn-reject {{
                background: rgba(239, 68, 68, 0.1);
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.2);
            }}
            .btn-reject:hover {{
                background: rgba(239, 68, 68, 0.2);
                transform: translateY(-2px);
            }}
            .loader {{
                display: none;
                border: 3px solid rgba(255, 255, 255, 0.1);
                border-top: 3px solid #38BDF8;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                margin: 20px auto 0;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .success-screen {{
                display: none;
            }}
            .success-icon {{
                width: 80px;
                height: 80px;
                background: rgba(16, 185, 129, 0.1);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
                color: #10B981;
                font-size: 40px;
            }}
        </style>
    </head>
    <body>
        <div class="card" id="mainCard">
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="24" height="24" rx="12" fill="#38BDF8" fill-opacity="0.2"/>
                    <path d="M12 6L6 12L12 18L18 12L12 6Z" stroke="#38BDF8" stroke-width="2" stroke-linejoin="round"/>
                </svg>
                <span>MERCADO PAGO (SIMULACIÓN)</span>
            </div>
            
            <div class="success-screen" id="successScreen">
                <div class="success-icon">✓</div>
                <h1 class="title">¡Pago Aprobado!</h1>
                <p class="subtitle" style="margin-bottom: 20px;">Tu pedido ha sido procesado correctamente y tu factura PDF fue generada.</p>
                <div style="font-size: 14px; color: #94A3B8; background: rgba(15, 23, 42, 0.3); border-radius: 12px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.02); line-height: 1.6; text-align: left;">
                    <strong>Orden ID:</strong> #{order.id}<br/>
                    <strong>Monto Total:</strong> ${order.total_amount:.2f}<br/>
                    <strong>Estado de Pago:</strong> Aprobado<br/>
                    <strong>Email:</strong> {order.user.email}
                </div>
            </div>
            
            <div class="payment-screen" id="paymentScreen">
                <h1 class="title">Pasarela de Pago</h1>
                <p class="subtitle">Mock de Integración para E-commerce API</p>
                
                <div class="order-summary">
                    <div class="summary-title">Resumen de Compra</div>
                    {items_html}
                    <div class="total-row">
                        <span>Total Neto:</span>
                        <span style="color: #38BDF8;">${order.total_amount:.2f}</span>
                    </div>
                </div>
                
                <div class="btn-group">
                    <button class="btn btn-approve" onclick="processPayment('approved')">Confirmar y Pagar</button>
                    <button class="btn btn-reject" onclick="processPayment('rejected')">Cancelar / Rechazar</button>
                </div>
                
                <div class="loader" id="loader"></div>
            </div>
        </div>

        <script>
            function processPayment(status) {{
                document.getElementById('loader').style.display = 'block';
                const buttons = document.querySelectorAll('.btn');
                buttons.forEach(btn => btn.disabled = true);
                
                fetch('/api/payments/webhook/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }},
                    body: JSON.stringify({{
                        payment_id: {payment.id},
                        status: status
                    }})
                }})
                .then(response => {{
                    document.getElementById('loader').style.display = 'none';
                    if (response.ok) {{
                        if (status === 'approved') {{
                            document.getElementById('paymentScreen').style.display = 'none';
                            document.getElementById('successScreen').style.display = 'block';
                        }} else {{
                            alert('Pago rechazado o cancelado.');
                        }}
                    }} else {{
                        alert('Error al procesar el pago en el servidor.');
                        buttons.forEach(btn => btn.disabled = false);
                    }}
                }})
                .catch(err => {{
                    document.getElementById('loader').style.display = 'none';
                    alert('Error de conexión: ' + err.message);
                    buttons.forEach(btn => btn.disabled = false);
                }});
            }}

            function getCookie(name) {{
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {{
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {{
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {{
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }}
                    }}
                }}
                return cookieValue;
            }}
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)