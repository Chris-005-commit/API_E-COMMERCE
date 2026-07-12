import io
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_invoice_pdf(invoice):
    """
    Genera un archivo PDF para la factura especificada usando reportlab
    y lo almacena en el campo pdf_file del modelo Invoice.
    """
    order = invoice.order
    user = order.user

    # Crear buffer en memoria
    buffer = io.BytesIO()

    # Configurar el documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    # Estilos
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados con colores premium
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1A365D') # Azul marino profundo
    )
    
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2D3748') # Gris oscuro
    )
    
    style_body = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4A5568') # Gris cuerpo
    )
    
    style_body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=style_body,
        fontName='Helvetica-Bold'
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=style_body,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []

    # 1. Cabecera (Grid de 2 columnas)
    header_data = [
        [
            Paragraph("<b>E-COMMERCE API</b><br/><font size=8 color='#718096'>Tu tienda de confianza</font>", style_title),
            Paragraph(f"<b>FACTURA</b><br/>"
                      f"<font size=10 color='#4A5568'>Número: {invoice.invoice_number}</font><br/>"
                      f"<font size=10 color='#4A5568'>Fecha: {invoice.issued_at.strftime('%d/%m/%Y')}</font>", ParagraphStyle('HeaderRight', parent=style_body, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[4.0*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # Línea decorativa azul
    divider = Table([[""]], colWidths=[7.5*inch])
    divider.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 2, colors.HexColor('#1A365D')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 20))

    # 2. Información del Cliente y del Pedido (Grid de 2 columnas)
    billing_data = [
        [
            Paragraph("<b>FACTURAR A:</b>", style_subtitle),
            Paragraph("<b>DETALLES DE LA ORDEN:</b>", style_subtitle)
        ],
        [
            Paragraph(f"<b>Nombre:</b> {user.first_name or user.username} {user.last_name}<br/>"
                      f"<b>Email:</b> {user.email or 'N/A'}", style_body),
            Paragraph(f"<b>Orden ID:</b> #{order.id}<br/>"
                      f"<b>Estado del Pedido:</b> {order.get_status_display()}<br/>"
                      f"<b>Fecha Creación:</b> {order.created_at.strftime('%d/%m/%Y %H:%M')}", style_body)
        ]
    ]
    billing_table = Table(billing_data, colWidths=[3.75*inch, 3.75*inch])
    billing_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(billing_table)
    story.append(Spacer(1, 25))

    # 3. Detalle de Ítems (Tabla con productos, precios, cantidades y subtotales)
    table_items_data = [
        [
            Paragraph("Producto (Variante)", style_table_header),
            Paragraph("Cantidad", style_table_header),
            Paragraph("Precio Unitario", style_table_header),
            Paragraph("Subtotal", style_table_header)
        ]
    ]

    for item in order.items.all():
        variant = item.product_variant
        variant_desc = f"{variant.product.name} (Talla: {variant.size}, Color: {variant.color})"
        subtotal = item.quantity * item.unit_price
        
        table_items_data.append([
            Paragraph(variant_desc, style_body),
            Paragraph(str(item.quantity), style_body),
            Paragraph(f"${item.unit_price:.2f}", style_body),
            Paragraph(f"${subtotal:.2f}", style_body)
        ])

    items_table = Table(table_items_data, colWidths=[3.8*inch, 1.0*inch, 1.3*inch, 1.4*inch])
    
    # Estilo de la tabla de ítems con alternancia de colores de fila
    items_table_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), # Encabezado azul marino
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), # Bordes muy finos en gris
    ]
    
    # Alternar fondos para filas de datos
    for i in range(1, len(table_items_data)):
        if i % 2 == 0:
            items_table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F7FAFC')))
            
    items_table.setStyle(TableStyle(items_table_style))
    story.append(items_table)
    story.append(Spacer(1, 20))

    # 4. Sección de Totales (Tabla en la esquina derecha)
    subtotal_bruto = sum(item.unit_price * item.quantity for item in order.items.all())
    discount_amount = max(0, subtotal_bruto - order.total_amount)

    totals_data = []
    if order.coupon:
        totals_data.append([Paragraph("<b>Subtotal Bruto:</b>", style_body), Paragraph(f"${subtotal_bruto:.2f}", style_body)])
        totals_data.append([Paragraph(f"<b>Descuento ({order.coupon.code} - {order.coupon.discount_percentage}%):</b>", style_body), Paragraph(f"-${discount_amount:.2f}", style_body)])
        totals_data.append([Paragraph("<b>Total Neto a Pagar:</b>", style_body_bold), Paragraph(f"${order.total_amount:.2f}", style_body_bold)])
    else:
        totals_data.append([Paragraph("<b>Subtotal:</b>", style_body), Paragraph(f"${order.total_amount:.2f}", style_body)])
        totals_data.append([Paragraph("<b>Total a Pagar:</b>", style_body_bold), Paragraph(f"${order.total_amount:.2f}", style_body_bold)])

    totals_table = Table(totals_data, colWidths=[2.2*inch, 1.0*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EDF2F7')), # Destacar la última fila (Total)
    ]))
    
    # Poner la tabla de totales alineada a la derecha
    totals_container_data = [
        ["", totals_table]
    ]
    totals_container = Table(totals_container_data, colWidths=[4.3*inch, 3.2*inch])
    totals_container.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(totals_container)
    story.append(Spacer(1, 40))

    # 5. Pie de página decorativo
    story.append(Spacer(1, 10))
    story.append(divider) # Línea divisoria azul inferior
    story.append(Spacer(1, 10))
    
    thanks_text = Paragraph("<center>¡Gracias por tu compra y preferencia!<br/>Esta es una factura generada automáticamente y es válida para fines contables oficiales.</center>", style_body)
    story.append(thanks_text)

    # Construir el documento PDF
    doc.build(story)

    # Obtener el contenido del buffer
    pdf_data = buffer.getvalue()
    buffer.close()

    # Guardar el PDF en el modelo
    filename = f"factura_{invoice.invoice_number}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_data), save=False)
    invoice.save()

    return filename
