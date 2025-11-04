from apps.venta.models import Venta, DetalleVenta
from django.db.models import Sum, Count, Q, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta


def report_ventas(filters):
    """
    Genera reporte de ventas con filtros personalizados
    
    Filtros disponibles:
    - fecha_inicio, fecha_fin: Rango de fechas
    - tipo_pago: 'contado' o 'credito'
    - estado_pago: 'pendiente', 'parcial', 'pagado'
    - cliente: ID del cliente
    - monto_min: Monto mínimo de venta
    - monto_max: Monto máximo de venta
    - orden: 'fecha', 'total', '-fecha', '-total' (- para descendente)
    """
    qs = Venta.objects.all().select_related('cliente')

    # Filtros de fecha
    if "fecha_inicio" in filters and "fecha_fin" in filters:
        qs = qs.filter(
            fecha__range=[filters["fecha_inicio"], filters["fecha_fin"]]
        )
    elif "fecha_inicio" in filters:
        qs = qs.filter(fecha__gte=filters["fecha_inicio"])
    elif "fecha_fin" in filters:
        qs = qs.filter(fecha__lte=filters["fecha_fin"])

    # Filtro por tipo de pago
    if "tipo_pago" in filters:
        qs = qs.filter(tipo_pago=filters["tipo_pago"])
    
    # Filtro por estado de pago
    if "estado_pago" in filters:
        qs = qs.filter(estado_pago=filters["estado_pago"])
    
    # Filtro por cliente
    if "cliente" in filters:
        qs = qs.filter(cliente_id=filters["cliente"])
    
    # Filtro por monto mínimo
    if "monto_min" in filters:
        qs = qs.filter(total__gte=filters["monto_min"])
    
    # Filtro por monto máximo
    if "monto_max" in filters:
        qs = qs.filter(total__lte=filters["monto_max"])
    
    # Ordenamiento
    orden = filters.get("orden", "-fecha")
    qs = qs.order_by(orden)

    # Agregaciones generales
    stats = qs.aggregate(
        total_ventas=Sum("total"),
        total_con_interes=Sum("total_con_interes"),
        cantidad_ventas=Count("id"),
        promedio_venta=Avg("total"),
        venta_maxima=Max("total"),
        venta_minima=Min("total")
    )

    total_ventas = float(stats["total_ventas"] or 0)
    total_con_interes = float(stats["total_con_interes"] or 0)
    cantidad = stats["cantidad_ventas"] or 0
    promedio = float(stats["promedio_venta"] or 0)
    venta_max = float(stats["venta_maxima"] or 0)
    venta_min = float(stats["venta_minima"] or 0)

    # Detalle por producto (usando VarianteProducto)
    detalle = (
        DetalleVenta.objects
        .filter(venta__in=qs)
        .values(
            "variante__producto__nombre",
            "variante__talla",
            "variante__color"
        )
        .annotate(
            total_vendido=Sum("cantidad"),
            monto_total=Sum("subtotal")
        )
        .order_by("-monto_total")
    )

    # Ventas por tipo de pago
    por_tipo_pago = (
        qs.values("tipo_pago")
        .annotate(
            cantidad=Count("id"),
            monto_total=Sum("total")
        )
    )

    # Ventas por estado de pago
    por_estado = (
        qs.values("estado_pago")
        .annotate(
            cantidad=Count("id"),
            monto_total=Sum("total")
        )
    )

    # Construcción del resumen
    fecha_inicio = filters.get('fecha_inicio', 'inicio')
    fecha_fin = filters.get('fecha_fin', 'hoy')
    
    return {
        "summary": f"Ventas entre {fecha_inicio} y {fecha_fin}",
        "columns": ["producto", "talla", "color", "cantidad_vendida", "total_bs"],
        "rows": [
            {
                "producto": d["variante__producto__nombre"],
                "talla": d["variante__talla"],
                "color": d["variante__color"],
                "cantidad_vendida": d["total_vendido"],
                "total_bs": float(d["monto_total"])
            }
            for d in detalle
        ],
        "meta": {
            "total_ventas": total_ventas,
            "total_con_interes": total_con_interes,
            "cantidad_ventas": cantidad,
            "promedio_venta": promedio,
            "venta_maxima": venta_max,
            "venta_minima": venta_min,
            "por_tipo_pago": [
                {
                    "tipo": t["tipo_pago"],
                    "cantidad": t["cantidad"],
                    "monto": float(t["monto_total"])
                }
                for t in por_tipo_pago
            ],
            "por_estado": [
                {
                    "estado": e["estado_pago"],
                    "cantidad": e["cantidad"],
                    "monto": float(e["monto_total"])
                }
                for e in por_estado
            ]
        },
    }


def report_ventas_por_cliente(cliente_id=None):
    """Reporte de ventas agrupadas por cliente"""
    qs = Venta.objects.all()
    
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    
    resumen = (
        qs.values(
            "cliente__email",
            "cliente__username",
            "cliente__first_name",
            "cliente__last_name"
        )
        .annotate(
            total_compras=Count("id"),
            monto_total=Sum("total"),
            monto_pendiente=Sum("total", filter=Q(estado_pago__in=['pendiente', 'parcial']))
        )
        .order_by("-monto_total")
    )
    
    return {
        "summary": "Ventas agrupadas por cliente",
        "columns": ["cliente", "username", "email", "total_compras", "monto_total", "monto_pendiente"],
        "rows": [
            {
                "cliente": f"{r['cliente__first_name']} {r['cliente__last_name']}".strip() or "Anónimo",
                "username": r["cliente__username"] or "N/A",
                "email": r["cliente__email"] or "N/A",
                "total_compras": r["total_compras"],
                "monto_total": float(r["monto_total"] or 0),
                "monto_pendiente": float(r["monto_pendiente"] or 0)
            }
            for r in resumen
        ]
    }


def report_ventas_por_periodo(periodo='mes'):
    """
    Reporte de ventas agrupadas por período
    periodo: 'dia', 'semana', 'mes', 'año'
    """
    from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, TruncYear
    
    trunc_functions = {
        'dia': TruncDay,
        'semana': TruncWeek,
        'mes': TruncMonth,
        'año': TruncYear
    }
    
    trunc_func = trunc_functions.get(periodo, TruncMonth)
    
    qs = Venta.objects.all()
    
    resumen = (
        qs.annotate(periodo=trunc_func('fecha'))
        .values('periodo')
        .annotate(
            cantidad_ventas=Count('id'),
            total_ventas=Sum('total'),
            ventas_contado=Count('id', filter=Q(tipo_pago='contado')),
            ventas_credito=Count('id', filter=Q(tipo_pago='credito'))
        )
        .order_by('-periodo')
    )
    
    return {
        "summary": f"Ventas agrupadas por {periodo}",
        "columns": ["periodo", "cantidad", "total", "contado", "credito"],
        "rows": [
            {
                "periodo": r["periodo"].strftime('%Y-%m-%d'),
                "cantidad": r["cantidad_ventas"],
                "total": float(r["total_ventas"] or 0),
                "contado": r["ventas_contado"],
                "credito": r["ventas_credito"]
            }
            for r in resumen
        ]
    }


def report_ventas_ultimos_dias(dias=30):
    """
    Reporte de ventas de los últimos N días
    """
    from datetime import datetime, timedelta
    
    hoy = datetime.now().date()
    fecha_inicio = hoy - timedelta(days=dias)
    
    return report_ventas({
        'fecha_inicio': str(fecha_inicio),
        'fecha_fin': str(hoy)
    })


def report_ventas_mayores_a(monto):
    """
    Reporte de ventas con monto mayor a X
    """
    from datetime import datetime, timedelta
    
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    return report_ventas({
        'fecha_inicio': str(hace_30_dias),
        'fecha_fin': str(hoy),
        'monto_min': monto,
        'orden': '-total'
    })


def report_ventas_menores_a(monto):
    """
    Reporte de ventas con monto menor a X
    """
    from datetime import datetime, timedelta
    
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    return report_ventas({
        'fecha_inicio': str(hace_30_dias),
        'fecha_fin': str(hoy),
        'monto_max': monto,
        'orden': 'total'
    })


def report_ventas_entre_montos(monto_min, monto_max):
    """
    Reporte de ventas con monto entre X y Y
    """
    from datetime import datetime, timedelta
    
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    return report_ventas({
        'fecha_inicio': str(hace_30_dias),
        'fecha_fin': str(hoy),
        'monto_min': monto_min,
        'monto_max': monto_max,
        'orden': '-total'
    })
