from apps.producto_variante.models import VarianteProducto
from apps.venta.models import DetalleVenta
from apps.productos.models import Producto
from apps.categorias.models import Categoria
from django.db.models import Sum, Count, Q, F, FloatField
from django.db.models.functions import Coalesce


def report_productos(filters):
    """
    Genera reporte de productos con filtros personalizados
    
    Filtros disponibles:
    - categoria: Nombre o ID de categoría
    - stock_bajo: Boolean para productos con stock <= stock_minimo
    - mas_vendidos: Boolean para ordenar por ventas
    - limite: Número máximo de resultados
    """
    qs = VarianteProducto.objects.all().select_related(
        'producto', 
        'producto__categoria'
    )

    # Filtro por categoría
    if "categoria" in filters:
        categoria_valor = filters["categoria"]
        # Intentar por nombre o ID
        try:
            categoria_id = int(categoria_valor)
            qs = qs.filter(producto__categoria_id=categoria_id)
        except (ValueError, TypeError):
            qs = qs.filter(
                producto__categoria__nombre__icontains=categoria_valor
            )

    # Filtro por stock bajo
    if filters.get("stock_bajo"):
        qs = qs.filter(stock__lte=F('stock_minimo'))

    data = []
    for variante in qs:
        # Calcular cantidad vendida
        vendidos = (
            DetalleVenta.objects
            .filter(variante=variante)
            .aggregate(total=Sum("cantidad"))["total"] or 0
        )
        
        # Calcular ingresos generados
        ingresos = (
            DetalleVenta.objects
            .filter(variante=variante)
            .aggregate(total=Sum("subtotal"))["total"] or 0
        )

        data.append({
            "id": variante.id,
            "producto": variante.producto.nombre,
            "categoria": variante.producto.categoria.nombre,
            "talla": variante.talla,
            "color": variante.color,
            "stock": variante.stock,
            "stock_minimo": variante.stock_minimo,
            "stock_critico": variante.stock <= variante.stock_minimo,
            "vendidos": vendidos,
            "precio_venta": float(variante.precio_venta),
            "precio_costo": float(variante.precio_costo),
            "ingresos": float(ingresos),
            "margen": float(variante.precio_venta - variante.precio_costo),
            "margen_porcentaje": round(
                ((variante.precio_venta - variante.precio_costo) / variante.precio_venta * 100), 2
            ) if variante.precio_venta > 0 else 0
        })

    # Ordenar por más vendidos si se especifica
    if filters.get("mas_vendidos"):
        data.sort(key=lambda x: x["vendidos"], reverse=True)
    
    # Limitar resultados
    limite = filters.get("limite")
    if limite:
        data = data[:int(limite)]

    # Estadísticas generales
    total_stock = sum(v["stock"] for v in data)
    total_vendidos = sum(v["vendidos"] for v in data)
    total_ingresos = sum(v["ingresos"] for v in data)
    productos_criticos = sum(1 for v in data if v["stock_critico"])

    return {
        "summary": f"Reporte de productos ({len(data)} variantes encontradas)",
        "columns": [
            "producto", "categoria", "talla", "color", "stock", 
            "vendidos", "precio_venta", "ingresos", "margen_porcentaje"
        ],
        "rows": data,
        "meta": {
            "total_variantes": len(data),
            "total_stock": total_stock,
            "total_vendidos": total_vendidos,
            "total_ingresos": total_ingresos,
            "productos_criticos": productos_criticos
        }
    }


def report_stock_bajo():
    """
    Reporte específico de productos con stock bajo o crítico
    """
    variantes_criticas = VarianteProducto.objects.filter(
        stock__lte=F('stock_minimo')
    ).select_related('producto', 'producto__categoria')

    data = []
    for variante in variantes_criticas:
        deficit = variante.stock_minimo - variante.stock
        
        data.append({
            "producto": variante.producto.nombre,
            "categoria": variante.producto.categoria.nombre,
            "talla": variante.talla,
            "color": variante.color,
            "stock_actual": variante.stock,
            "stock_minimo": variante.stock_minimo,
            "deficit": deficit,
            "estado": "CRÍTICO" if variante.stock == 0 else "BAJO"
        })

    return {
        "summary": f"Productos con stock bajo ({len(data)} variantes)",
        "columns": [
            "producto", "categoria", "talla", "color", 
            "stock_actual", "stock_minimo", "deficit", "estado"
        ],
        "rows": data,
        "meta": {
            "total_productos_criticos": len(data),
            "sin_stock": sum(1 for v in data if v["stock_actual"] == 0)
        }
    }


def report_productos_mas_vendidos(limite=10):
    """
    Top N productos más vendidos
    """
    vendidos = (
        DetalleVenta.objects
        .values(
            'variante__id',
            'variante__producto__nombre',
            'variante__talla',
            'variante__color',
            'variante__precio_venta',
            'variante__stock'
        )
        .annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos_totales=Sum('subtotal'),
            num_ventas=Count('venta', distinct=True)
        )
        .order_by('-cantidad_vendida')[:limite]
    )

    return {
        "summary": f"Top {limite} productos más vendidos",
        "columns": [
            "producto", "talla", "color", "cantidad_vendida", 
            "num_ventas", "ingresos", "stock_actual"
        ],
        "rows": [
            {
                "producto": v["variante__producto__nombre"],
                "talla": v["variante__talla"],
                "color": v["variante__color"],
                "cantidad_vendida": v["cantidad_vendida"],
                "num_ventas": v["num_ventas"],
                "ingresos": float(v["ingresos_totales"]),
                "stock_actual": v["variante__stock"]
            }
            for v in vendidos
        ]
    }


def report_productos_sin_ventas():
    """
    Productos que nunca se han vendido
    """
    # Obtener IDs de variantes que SÍ se han vendido
    variantes_vendidas = DetalleVenta.objects.values_list(
        'variante_id', flat=True
    ).distinct()

    # Filtrar variantes que NO están en esa lista
    sin_ventas = VarianteProducto.objects.exclude(
        id__in=variantes_vendidas
    ).select_related('producto', 'producto__categoria')

    data = []
    for variante in sin_ventas:
        data.append({
            "producto": variante.producto.nombre,
            "categoria": variante.producto.categoria.nombre,
            "talla": variante.talla,
            "color": variante.color,
            "stock": variante.stock,
            "precio_venta": float(variante.precio_venta),
            "valor_inventario": float(variante.stock * variante.precio_costo)
        })

    total_valor = sum(v["valor_inventario"] for v in data)

    return {
        "summary": f"Productos sin ventas ({len(data)} variantes)",
        "columns": [
            "producto", "categoria", "talla", "color", 
            "stock", "precio_venta", "valor_inventario"
        ],
        "rows": data,
        "meta": {
            "total_productos": len(data),
            "valor_total_inventario": total_valor
        }
    }


def report_rentabilidad_productos():
    """
    Análisis de rentabilidad por producto
    """
    rentabilidad = (
        DetalleVenta.objects
        .values(
            'variante__producto__nombre',
            'variante__precio_venta',
            'variante__precio_costo'
        )
        .annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos=Sum('subtotal')
        )
    )

    data = []
    for r in rentabilidad:
        precio_venta = float(r['variante__precio_venta'])
        precio_costo = float(r['variante__precio_costo'])
        cantidad = r['cantidad_vendida']
        ingresos = float(r['ingresos'])
        
        costo_total = precio_costo * cantidad
        ganancia_neta = ingresos - costo_total
        margen_porcentaje = ((precio_venta - precio_costo) / precio_venta * 100) if precio_venta > 0 else 0

        data.append({
            "producto": r['variante__producto__nombre'],
            "cantidad_vendida": cantidad,
            "ingresos": ingresos,
            "costo_total": costo_total,
            "ganancia_neta": ganancia_neta,
            "margen_porcentaje": round(margen_porcentaje, 2)
        })

    # Ordenar por ganancia neta
    data.sort(key=lambda x: x["ganancia_neta"], reverse=True)

    total_ingresos = sum(d["ingresos"] for d in data)
    total_costos = sum(d["costo_total"] for d in data)
    ganancia_total = total_ingresos - total_costos

    return {
        "summary": "Análisis de rentabilidad por producto",
        "columns": [
            "producto", "cantidad_vendida", "ingresos", 
            "costo_total", "ganancia_neta", "margen_porcentaje"
        ],
        "rows": data,
        "meta": {
            "total_ingresos": total_ingresos,
            "total_costos": total_costos,
            "ganancia_total": ganancia_total,
            "margen_promedio": round((ganancia_total / total_ingresos * 100), 2) if total_ingresos > 0 else 0
        }
    }


def report_productos_menos_vendidos(limite=10):
    """
    Productos con menos ventas (excluyendo los que no tienen ventas)
    """
    vendidos = (
        DetalleVenta.objects
        .values(
            'variante__id',
            'variante__producto__nombre',
            'variante__talla',
            'variante__color',
            'variante__precio_venta',
            'variante__stock'
        )
        .annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos_totales=Sum('subtotal'),
            num_ventas=Count('venta', distinct=True)
        )
        .order_by('cantidad_vendida')[:limite]  # Ordenar ascendente
    )

    return {
        "summary": f"Top {limite} productos menos vendidos",
        "columns": [
            "producto", "talla", "color", "cantidad_vendida", 
            "num_ventas", "ingresos", "stock_actual"
        ],
        "rows": [
            {
                "producto": v["variante__producto__nombre"],
                "talla": v["variante__talla"],
                "color": v["variante__color"],
                "cantidad_vendida": v["cantidad_vendida"],
                "num_ventas": v["num_ventas"],
                "ingresos": float(v["ingresos_totales"]),
                "stock_actual": v["variante__stock"]
            }
            for v in vendidos
        ]
    }


def report_productos_que_generaron_mas_ingresos(limite=10):
    """
    Productos que generaron más ingresos (dinero)
    """
    por_ingresos = (
        DetalleVenta.objects
        .values(
            'variante__id',
            'variante__producto__nombre',
            'variante__talla',
            'variante__color',
            'variante__precio_venta'
        )
        .annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos_totales=Sum('subtotal'),
            num_ventas=Count('venta', distinct=True)
        )
        .order_by('-ingresos_totales')[:limite]
    )

    return {
        "summary": f"Top {limite} productos que generaron más ingresos",
        "columns": [
            "producto", "talla", "color", "ingresos_totales", 
            "cantidad_vendida", "precio_promedio"
        ],
        "rows": [
            {
                "producto": v["variante__producto__nombre"],
                "talla": v["variante__talla"],
                "color": v["variante__color"],
                "ingresos_totales": float(v["ingresos_totales"]),
                "cantidad_vendida": v["cantidad_vendida"],
                "precio_promedio": float(v["ingresos_totales"] / v["cantidad_vendida"]) if v["cantidad_vendida"] > 0 else 0
            }
            for v in por_ingresos
        ]
    }


def report_productos_que_generaron_menos_ingresos(limite=10):
    """
    Productos que generaron menos ingresos
    """
    por_ingresos = (
        DetalleVenta.objects
        .values(
            'variante__id',
            'variante__producto__nombre',
            'variante__talla',
            'variante__color',
            'variante__precio_venta'
        )
        .annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos_totales=Sum('subtotal'),
            num_ventas=Count('venta', distinct=True)
        )
        .order_by('ingresos_totales')[:limite]  
    )

    return {
        "summary": f"Top {limite} productos que generaron menos ingresos",
        "columns": [
            "producto", "talla", "color", "ingresos_totales", 
            "cantidad_vendida", "precio_promedio"
        ],
        "rows": [
            {
                "producto": v["variante__producto__nombre"],
                "talla": v["variante__talla"],
                "color": v["variante__color"],
                "ingresos_totales": float(v["ingresos_totales"]),
                "cantidad_vendida": v["cantidad_vendida"],
                "precio_promedio": float(v["ingresos_totales"] / v["cantidad_vendida"]) if v["cantidad_vendida"] > 0 else 0
            }
            for v in por_ingresos
        ]
    }
