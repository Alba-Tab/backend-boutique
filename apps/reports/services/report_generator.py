from .natural_language_parser.ventas_parser import parse_query
from .products_report_service import (
    report_productos,
    report_stock_bajo,
    report_productos_mas_vendidos,
    report_productos_sin_ventas,
    report_rentabilidad_productos,
    report_productos_menos_vendidos,
    report_productos_que_generaron_mas_ingresos,
    report_productos_que_generaron_menos_ingresos
)
from .ventas_report_service import (
    report_ventas,
    report_ventas_por_cliente,
    report_ventas_por_periodo,
    report_ventas_ultimos_dias,
    report_ventas_mayores_a,
    report_ventas_menores_a,
    report_ventas_entre_montos
)
from .pagos_report_service import (
    report_pagos,
    report_cuotas,
    report_morosidad,
    report_flujo_caja
)


def generate_report(query_text: str):
    """
    Genera un reporte basado en lenguaje natural
    
    Ejemplos:
    - "ventas del último mes"
    - "Muéstrame un reporte de ventas de este mes mayores cuya cantidad vendida sea mayor a 15"
    - "dame los productos mas vendidos de este mes"
    - "dame los productos mas vendidos del anterior mes"
    - "dame los 5 productos menos vendidos"
    - "Muéstrame un reporte de ventas de este mes con el producto mas vendido"
    """
    parsed = parse_query(query_text)
    intent = parsed.get("intent")
    filters = parsed.get("filters", {})
    limit = parsed.get("limit")

    # ========== REPORTES DE VENTAS ==========
    
    # Ventas con rangos de montos
    if intent == "ventas_mayores_a":
        monto = filters.get("monto_min", 0)
        result = report_ventas_mayores_a(monto)
        # Aplicar filtros adicionales si existen
        if filters.get("fecha_inicio"):
            result = _apply_date_filter(result, filters)
        if filters.get("cantidad_min"):
            result = _apply_quantity_filter(result, filters)
    
    elif intent == "ventas_menores_a":
        monto = filters.get("monto_max", 10000)
        result = report_ventas_menores_a(monto)
        if filters.get("fecha_inicio"):
            result = _apply_date_filter(result, filters)
        if filters.get("cantidad_min"):
            result = _apply_quantity_filter(result, filters)
    
    elif intent == "ventas_entre_montos":
        monto_min = filters.get("monto_min", 0)
        monto_max = filters.get("monto_max", 10000)
        result = report_ventas_entre_montos(monto_min, monto_max)
        if filters.get("fecha_inicio"):
            result = _apply_date_filter(result, filters)
        if filters.get("cantidad_min"):
            result = _apply_quantity_filter(result, filters)
    
    # Ventas con producto más vendido
    elif intent == "ventas_con_producto":
        result = _report_ventas_con_producto_mas_vendido(filters)
    
    # Ventas generales
    elif intent == "ventas":
        result = report_ventas(filters)
        
    elif intent == "ventas_cliente":
        result = report_ventas_por_cliente(filters.get("cliente"))
    
    elif intent == "ventas_periodo":
        result = report_ventas_por_periodo(filters.get("periodo", "mes"))
    
    # ========== REPORTES DE PRODUCTOS ==========
    
    # Productos más vendidos
    elif intent == "productos_mas_vendidos":
        limite = limit or 10
        # Si hay filtro de fechas, aplicar
        if filters.get("fecha_inicio"):
            result = _report_productos_mas_vendidos_con_fechas(limite, filters)
        else:
            result = report_productos_mas_vendidos(limite)
    
    # Productos menos vendidos
    elif intent == "productos_menos_vendidos":
        limite = limit or 10
        if filters.get("fecha_inicio"):
            result = _report_productos_menos_vendidos_con_fechas(limite, filters)
        else:
            result = report_productos_menos_vendidos(limite)
    
    # Productos que generaron más ingresos
    elif intent == "productos_mas_ingresos":
        limite = limit or 10
        result = report_productos_que_generaron_mas_ingresos(limite)
    
    # Productos que generaron menos ingresos
    elif intent == "productos_menos_ingresos":
        limite = limit or 10
        result = report_productos_que_generaron_menos_ingresos(limite)
    
    # Productos generales
    elif intent == "productos":
        result = report_productos(filters)
    
    elif intent == "stock_bajo":
        result = report_stock_bajo()
    
    elif intent == "sin_ventas":
        result = report_productos_sin_ventas()
    
    elif intent == "rentabilidad":
        result = report_rentabilidad_productos()
    
    # ========== REPORTES DE PAGOS Y CUOTAS ==========
    
    elif intent == "pagos":
        result = report_pagos(filters)
    
    elif intent == "cuotas":
        result = report_cuotas(filters)
    
    elif intent == "morosidad":
        result = report_morosidad()
    
    elif intent == "flujo_caja":
        result = report_flujo_caja(filters)
    
    else:
        result = {
            "summary": "Tipo de reporte no reconocido.",
            "columns": [],
            "rows": [],
            "meta": {
                "error": f"Intent '{intent}' no reconocido",
                "sugerencias": [
                    "ventas del mes mayores a 1000",
                    "productos más vendidos de este mes",
                    "los 5 productos menos vendidos",
                    "ventas de este mes con el producto más vendido",
                    "productos que generaron más ingresos",
                    "stock bajo",
                    "cuotas vencidas",
                    "morosidad"
                ]
            }
        }

    return {
        "query_original": query_text,
        "parsed_query": parsed,
        "report": result
    }


def generate_report_by_type(report_type: str, filters: dict = None):
    """
    Genera un reporte directamente por tipo, sin parseo de lenguaje natural
    
    Args:
        report_type: Tipo de reporte ('ventas', 'productos', 'pagos', etc.)
        filters: Diccionario de filtros
    
    Returns:
        Dict con el resultado del reporte
    """
    filters = filters or {}
    
    # Mapeo directo de tipos de reporte
    report_map = {
        # Ventas
        'ventas': lambda: report_ventas(filters),
        'ventas_cliente': lambda: report_ventas_por_cliente(filters.get('cliente')),
        'ventas_periodo': lambda: report_ventas_por_periodo(filters.get('periodo', 'mes')),
        'ventas_ultimos_dias': lambda: report_ventas_ultimos_dias(filters.get('dias', 30)),
        'ventas_mayores_a': lambda: report_ventas_mayores_a(filters.get('monto', 0)),
        'ventas_menores_a': lambda: report_ventas_menores_a(filters.get('monto', 1000)),
        'ventas_entre_montos': lambda: report_ventas_entre_montos(
            filters.get('monto_min', 0), 
            filters.get('monto_max', 10000)
        ),
        
        # Productos
        'productos': lambda: report_productos(filters),
        'stock_bajo': lambda: report_stock_bajo(),
        'mas_vendidos': lambda: report_productos_mas_vendidos(filters.get('limite', 10)),
        'menos_vendidos': lambda: report_productos_menos_vendidos(filters.get('limite', 10)),
        'sin_ventas': lambda: report_productos_sin_ventas(),
        'rentabilidad': lambda: report_rentabilidad_productos(),
        'productos_mas_ingresos': lambda: report_productos_que_generaron_mas_ingresos(filters.get('limite', 10)),
        'productos_menos_ingresos': lambda: report_productos_que_generaron_menos_ingresos(filters.get('limite', 10)),
        
        # Pagos y cuotas
        'pagos': lambda: report_pagos(filters),
        'cuotas': lambda: report_cuotas(filters),
        'morosidad': lambda: report_morosidad(),
        'flujo_caja': lambda: report_flujo_caja(filters),
    }
    
    if report_type in report_map:
        result = report_map[report_type]()
        return {
            "report_type": report_type,
            "filters": filters,
            "report": result
        }
    else:
        return {
            "report_type": report_type,
            "filters": filters,
            "report": {
                "summary": f"Tipo de reporte '{report_type}' no encontrado",
                "columns": [],
                "rows": [],
                "meta": {
                    "error": "Tipo de reporte inválido",
                    "tipos_disponibles": list(report_map.keys())
                }
            }
        }


# ========== FUNCIONES AUXILIARES PARA FILTROS COMBINADOS ==========

def _apply_date_filter(result, filters):
    """
    Filtra las ventas por rango de fechas.
    """
    from datetime import datetime
    
    fecha_inicio = filters.get('fecha_inicio')
    fecha_fin = filters.get('fecha_fin')
    
    if not fecha_inicio or not fecha_fin:
        return result
    
    fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
    fecha_fin_dt = datetime.fromisoformat(fecha_fin)
    
    ventas_filtradas = [
        venta for venta in result.get('ventas', [])
        if fecha_inicio_dt <= datetime.fromisoformat(venta['fecha'].replace('Z', '+00:00')) <= fecha_fin_dt
    ]
    
    result['ventas'] = ventas_filtradas
    result['total_ventas'] = len(ventas_filtradas)
    
    # Recalcular monto_total
    from decimal import Decimal
    monto_total = sum(Decimal(str(v['total'])) for v in ventas_filtradas)
    result['monto_total'] = str(monto_total)
    
    return result


def _apply_quantity_filter(result, filters):
    """
    Filtra las ventas por cantidad vendida.
    Requiere que las ventas tengan detalles de productos.
    """
    cantidad_min = filters.get('cantidad_min')
    cantidad_max = filters.get('cantidad_max')
    
    if not cantidad_min and not cantidad_max:
        return result
    
    from apps.venta.models import DetalleVenta
    
    ventas_filtradas = []
    for venta in result.get('ventas', []):
        # Obtener la suma de cantidades de esta venta
        detalles = DetalleVenta.objects.filter(venta_id=venta['id'])
        cantidad_total = sum(detalle.cantidad for detalle in detalles)
        
        # Aplicar filtro
        cumple_filtro = True
        if cantidad_min and cantidad_total < cantidad_min:
            cumple_filtro = False
        if cantidad_max and cantidad_total > cantidad_max:
            cumple_filtro = False
        
        if cumple_filtro:
            venta['cantidad_total_productos'] = cantidad_total
            ventas_filtradas.append(venta)
    
    result['ventas'] = ventas_filtradas
    result['total_ventas'] = len(ventas_filtradas)
    
    # Recalcular monto_total
    from decimal import Decimal
    monto_total = sum(Decimal(str(v['total'])) for v in ventas_filtradas)
    result['monto_total'] = str(monto_total)
    
    return result


def _report_ventas_con_producto_mas_vendido(filters):
    """
    Genera un reporte de ventas que incluye información del producto más vendido.
    """
    from apps.producto_variante.models import VarianteProducto
    from apps.venta.models import Venta, DetalleVenta
    from django.db.models import Sum, Count
    from datetime import datetime
    
    # Obtener el producto más vendido en el período
    query_detalles = DetalleVenta.objects.all()
    
    # Aplicar filtro de fechas si existe
    if filters.get('fecha_inicio') and filters.get('fecha_fin'):
        fecha_inicio = datetime.fromisoformat(filters['fecha_inicio'])
        fecha_fin = datetime.fromisoformat(filters['fecha_fin'])
        query_detalles = query_detalles.filter(
            venta__fecha__gte=fecha_inicio,
            venta__fecha__lte=fecha_fin
        )
    
    # Encontrar el producto más vendido
    producto_mas_vendido = query_detalles.values(
        'variante_producto__id',
        'variante_producto__producto__nombre',
        'variante_producto__sku'
    ).annotate(
        cantidad_total=Sum('cantidad')
    ).order_by('-cantidad_total').first()
    
    if not producto_mas_vendido:
        return {
            "ventas": [],
            "total_ventas": 0,
            "monto_total": "0.00",
            "producto_mas_vendido": None,
            "mensaje": "No se encontraron ventas en el período especificado"
        }
    
    # Obtener las ventas que incluyen ese producto
    variante_id = producto_mas_vendido['variante_producto__id']
    ventas_con_producto = Venta.objects.filter(
        detalleventa__variante_producto_id=variante_id
    ).distinct()
    
    # Aplicar filtro de fechas a las ventas también
    if filters.get('fecha_inicio') and filters.get('fecha_fin'):
        ventas_con_producto = ventas_con_producto.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        )
    
    # Serializar ventas
    ventas_data = []
    for venta in ventas_con_producto:
        ventas_data.append({
            "id": venta.id,
            "codigo": venta.codigo,
            "fecha": venta.fecha.isoformat(),
            "cliente": f"{venta.cliente.first_name} {venta.cliente.last_name}" if venta.cliente.first_name else venta.cliente.username,
            "total": str(venta.total),
            "total_con_interes": str(venta.total_con_interes),
            "tipo_venta": venta.tipo_venta
        })
    
    from decimal import Decimal
    monto_total = sum(Decimal(str(v['total'])) for v in ventas_data)
    
    return {
        "ventas": ventas_data,
        "total_ventas": len(ventas_data),
        "monto_total": str(monto_total),
        "producto_mas_vendido": {
            "nombre": producto_mas_vendido['variante_producto__producto__nombre'],
            "sku": producto_mas_vendido['variante_producto__sku'],
            "cantidad_vendida": producto_mas_vendido['cantidad_total']
        },
        "stats": {
            "promedio_venta": str(monto_total / len(ventas_data)) if ventas_data else "0.00"
        }
    }


def _report_productos_mas_vendidos_con_fechas(limite, filters):
    """
    Obtiene los productos más vendidos en un rango de fechas específico.
    """
    from apps.producto_variante.models import VarianteProducto
    from apps.venta.models import DetalleVenta
    from django.db.models import Sum, Count
    from datetime import datetime
    
    query = DetalleVenta.objects.select_related(
        'variante_producto',
        'variante_producto__producto',
        'variante_producto__producto__categoria'
    )
    
    # Aplicar filtro de fechas
    if filters.get('fecha_inicio') and filters.get('fecha_fin'):
        fecha_inicio = datetime.fromisoformat(filters['fecha_inicio'])
        fecha_fin = datetime.fromisoformat(filters['fecha_fin'])
        query = query.filter(
            venta__fecha__gte=fecha_inicio,
            venta__fecha__lte=fecha_fin
        )
    
    # Agrupar y ordenar
    productos = query.values(
        'variante_producto__id',
        'variante_producto__producto__nombre',
        'variante_producto__sku',
        'variante_producto__color',
        'variante_producto__talla'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        ingresos_generados=Sum('subtotal')
    ).order_by('-cantidad_vendida')[:limite]
    
    productos_data = []
    for p in productos:
        productos_data.append({
            "id": p['variante_producto__id'],
            "nombre": p['variante_producto__producto__nombre'],
            "sku": p['variante_producto__sku'],
            "color": p['variante_producto__color'],
            "talla": p['variante_producto__talla'],
            "cantidad_vendida": p['cantidad_vendida'],
            "ingresos_generados": str(p['ingresos_generados'])
        })
    
    return {
        "productos": productos_data,
        "periodo": {
            "fecha_inicio": filters.get('fecha_inicio'),
            "fecha_fin": filters.get('fecha_fin')
        }
    }


def _report_productos_menos_vendidos_con_fechas(limite, filters):
    """
    Obtiene los productos menos vendidos en un rango de fechas específico.
    """
    from apps.producto_variante.models import VarianteProducto
    from apps.venta.models import DetalleVenta
    from django.db.models import Sum, Count
    from datetime import datetime
    
    query = DetalleVenta.objects.select_related(
        'variante_producto',
        'variante_producto__producto',
        'variante_producto__producto__categoria'
    )
    
    # Aplicar filtro de fechas
    if filters.get('fecha_inicio') and filters.get('fecha_fin'):
        fecha_inicio = datetime.fromisoformat(filters['fecha_inicio'])
        fecha_fin = datetime.fromisoformat(filters['fecha_fin'])
        query = query.filter(
            venta__fecha__gte=fecha_inicio,
            venta__fecha__lte=fecha_fin
        )
    
    # Agrupar y ordenar (ascendente por cantidad)
    productos = query.values(
        'variante_producto__id',
        'variante_producto__producto__nombre',
        'variante_producto__sku',
        'variante_producto__color',
        'variante_producto__talla'
    ).annotate(
        cantidad_vendida=Sum('cantidad'),
        ingresos_generados=Sum('subtotal')
    ).order_by('cantidad_vendida')[:limite]  # Ascendente para los menos vendidos
    
    productos_data = []
    for p in productos:
        productos_data.append({
            "id": p['variante_producto__id'],
            "nombre": p['variante_producto__producto__nombre'],
            "sku": p['variante_producto__sku'],
            "color": p['variante_producto__color'],
            "talla": p['variante_producto__talla'],
            "cantidad_vendida": p['cantidad_vendida'],
            "ingresos_generados": str(p['ingresos_generados'])
        })
    
    return {
        "productos": productos_data,
        "periodo": {
            "fecha_inicio": filters.get('fecha_inicio'),
            "fecha_fin": filters.get('fecha_fin')
        }
    }
