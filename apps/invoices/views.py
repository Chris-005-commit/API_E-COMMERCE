from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                return Invoice.objects.all()
            return Invoice.objects.filter(order__user=user)
        return Invoice.objects.none()

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        invoice = self.get_object()
        if not invoice.pdf_file:
            return Response(
                {"detail": "El archivo PDF no está disponible para esta factura."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            return FileResponse(
                invoice.pdf_file.open('rb'),
                content_type='application/pdf',
                as_attachment=True,
                filename=f"factura_{invoice.invoice_number}.pdf"
            )
        except FileNotFoundError:
            return Response(
                {"detail": "El archivo PDF no se encontró en el servidor."},
                status=status.HTTP_404_NOT_FOUND
            )
