from apps.pago.models import Pago
from apps.cuota.models import CuotaCredito
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone


def report_pagos(filters):
    """
    Genera reporte de pagos con filtros personalizados
    
    Filtros disponibles:
    - fecha_inicio, fecha_fin: Rango de fechas
    - metodo_pago: 'efectivo', 'tarjeta', 'qr'
    - venta: ID de la venta
    - cliente: ID del cliente
    """
    qs = Pago.objects.all().select_related('venta', 'venta__cliente', 'cuota')

    # Filtros de fecha
    if "fecha_inicio" in filters and "fecha_fin" in filters:
        qs = qs.filter(
            fecha_pago__range=[filters["fecha_inicio"], filters["fecha_fin"]]
        )
    elif "fecha_inicio" in filters:
        qs = qs.filter(fecha_pago__gte=filters["fecha_inicio"])
    elif "fecha_fin" in filters:
        qs = qs.filter(fecha_pago__lte=filters["fecha_fin"])

    # Filtro por método de pago
    if "metodo_pago" in filters:
        qs = qs.filter(metodo_pago=filters["metodo_pago"])
    
    # Filtro por venta
    if "venta" in filters:
        qs = qs.filter(venta_id=filters["venta"])
    
    # Filtro por cliente
    if "cliente" in filters:
        qs = qs.filter(venta__cliente_id=filters["cliente"])

    # Agregaciones generales
    stats = qs.aggregate(
        total_pagos=Sum("monto_pagado"),
        cantidad_pagos=Count("id"),
        promedio_pago=Avg("monto_pagado")
    )

    total_pagos = float(stats["total_pagos"] or 0)
    cantidad = stats["cantidad_pagos"] or 0
    promedio = float(stats["promedio_pago"] or 0)

    # Resumen por método de pago
    resumen_metodo = (
        qs.values("metodo_pago")
        .annotate(
            cantidad=Count("id"),
            total_monto=Sum("monto_pagado")
        )
        .order_by("-total_monto")
    )

    # Pagos vinculados a cuotas vs pagos directos
    pagos_con_cuota = qs.filter(cuota__isnull=False).count()
    pagos_directos = qs.filter(cuota__isnull=True).count()

    fecha_inicio = filters.get('fecha_inicio', 'inicio')
    fecha_fin = filters.get('fecha_fin', 'hoy')

    return {
        "summary": f"Reporte de pagos entre {fecha_inicio} y {fecha_fin}",
        "columns": ["método_pago", "cantidad_pagos", "monto_total"],
        "rows": [
            {
                "método_pago": r["metodo_pago"],
                "cantidad_pagos": r["cantidad"],
                "monto_total": float(r["total_monto"])
            }
            for r in resumen_metodo
        ],
        "meta": {
            "total_pagos": total_pagos,
            "cantidad_pagos": cantidad,
            "promedio_pago": promedio,
            "pagos_con_cuota": pagos_con_cuota,
            "pagos_directos": pagos_directos
        }
    }


def report_cuotas(filters):
    """
    Genera reporte de cuotas de crédito
    
    Filtros disponibles:
    - estado: 'pendiente', 'pagada', 'vencida'
    - venta: ID de la venta
    - cliente: ID del cliente
    - vencimiento_desde, vencimiento_hasta: Rango de vencimiento
    """
    qs = CuotaCredito.objects.all().select_related('venta', 'venta__cliente')

    # Filtro por estado
    if "estado" in filters:
        qs = qs.filter(estado=filters["estado"])
    
    # Filtro por venta
    if "venta" in filters:
        qs = qs.filter(venta_id=filters["venta"])
    
    # Filtro por cliente
    if "cliente" in filters:
        qs = qs.filter(venta__cliente_id=filters["cliente"])
    
    # Filtro por fecha de vencimiento
    if "vencimiento_desde" in filters and "vencimiento_hasta" in filters:
        qs = qs.filter(
            fecha_vencimiento__range=[
                filters["vencimiento_desde"],
                filters["vencimiento_hasta"]
            ]
        )

    # Agregaciones generales
    stats = qs.aggregate(
        total_monto=Sum("monto_cuota"),
        cantidad_cuotas=Count("id")
    )

    total_monto = float(stats["total_monto"] or 0)
    cantidad = stats["cantidad_cuotas"] or 0

    # Resumen por estado
    resumen_estado = (
        qs.values("estado")
        .annotate(
            cantidad=Count("id"),
            total_monto=Sum("monto_cuota")
        )
        .order_by("-total_monto")
    )

    # Cuotas vencidas (no pagadas y fecha pasada)
    hoy = timezone.now().date()
    cuotas_vencidas = qs.filter(
        estado__in=['pendiente'],
        fecha_vencimiento__lt=hoy
    ).count()

    return {
        "summary": "Reporte de cuotas de crédito",
        "columns": ["estado", "cantidad_cuotas", "monto_total"],
        "rows": [
            {
                "estado": r["estado"],
                "cantidad_cuotas": r["cantidad"],
                "monto_total": float(r["total_monto"])
            }
            for r in resumen_estado
        ],
        "meta": {
            "total_monto": total_monto,
            "cantidad_cuotas": cantidad,
            "cuotas_vencidas": cuotas_vencidas
        }
    }


def report_morosidad():
    """
    Reporte de morosidad: cuotas vencidas y clientes con deuda
    """
    hoy = timezone.now().date()
    
    # Cuotas vencidas
    cuotas_vencidas = CuotaCredito.objects.filter(
        estado='pendiente',
        fecha_vencimiento__lt=hoy
    ).select_related('venta', 'venta__cliente')
    
    # Agrupar por cliente
    clientes_morosos = (
        cuotas_vencidas
        .values(
            'venta__cliente__email',
            'venta__cliente__username',
            'venta__cliente__first_name',
            'venta__cliente__last_name'
        )
        .annotate(
            cuotas_vencidas=Count('id'),
            monto_vencido=Sum('monto_cuota')
        )
        .order_by('-monto_vencido')
    )
    
    return {
        "summary": "Reporte de morosidad",
        "columns": ["cliente", "username", "email", "cuotas_vencidas", "monto_vencido"],
        "rows": [
            {
                "cliente": f"{c['venta__cliente__first_name']} {c['venta__cliente__last_name']}".strip() or "Anónimo",
                "username": c["venta__cliente__username"] or "N/A",
                "email": c["venta__cliente__email"] or "N/A",
                "cuotas_vencidas": c["cuotas_vencidas"],
                "monto_vencido": float(c["monto_vencido"])
            }
            for c in clientes_morosos
        ],
        "meta": {
            "total_cuotas_vencidas": cuotas_vencidas.count(),
            "total_monto_vencido": float(cuotas_vencidas.aggregate(
                total=Sum('monto_cuota')
            )['total'] or 0)
        }
    }


def report_flujo_caja(filters):
    """
    Reporte de flujo de caja: pagos recibidos vs ventas realizadas
    """
    fecha_inicio = filters.get('fecha_inicio')
    fecha_fin = filters.get('fecha_fin')
    
    # Pagos recibidos (dinero que ENTRA)
    qs_pagos = Pago.objects.all()
    if fecha_inicio and fecha_fin:
        qs_pagos = qs_pagos.filter(fecha_pago__range=[fecha_inicio, fecha_fin])
    
    ingresos = qs_pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0
    
    # Ventas realizadas (dinero por COBRAR)
    from apps.venta.models import Venta
    qs_ventas = Venta.objects.all()
    if fecha_inicio and fecha_fin:
        qs_ventas = qs_ventas.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    ventas_totales = qs_ventas.aggregate(total=Sum('total'))['total'] or 0
    ventas_pendientes = qs_ventas.filter(
        estado_pago__in=['pendiente', 'parcial']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    return {
        "summary": f"Flujo de caja del {fecha_inicio} al {fecha_fin}",
        "columns": ["concepto", "monto"],
        "rows": [
            {"concepto": "Ingresos (pagos recibidos)", "monto": float(ingresos)},
            {"concepto": "Ventas totales", "monto": float(ventas_totales)},
            {"concepto": "Por cobrar (pendiente)", "monto": float(ventas_pendientes)},
        ],
        "meta": {
            "ingresos_reales": float(ingresos),
            "por_cobrar": float(ventas_pendientes),
            "efectividad_cobranza": round((float(ingresos) / float(ventas_totales) * 100), 2) if ventas_totales > 0 else 0
        }
    }
