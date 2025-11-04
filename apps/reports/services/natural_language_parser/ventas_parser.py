import re
from .base_parser import (
    extract_dates, 
    extract_order, 
    extract_limit, 
    extract_amount_filters,
    extract_quantity_filters,
    detect_report_type
)
from .errors import UnknownReportError

def parse_ventas_query(text):
    filters = extract_dates(text)
    order_by = extract_order(text)
    limit = extract_limit(text)
    
    # Agregar filtros de monto
    amount_filters = extract_amount_filters(text)
    filters.update(amount_filters)
    
    # Agregar filtros de cantidad
    quantity_filters = extract_quantity_filters(text)
    filters.update(quantity_filters)
    
    # Detectar si pide ordenamiento específico
    if order_by:
        filters['orden'] = order_by

    return {
        "intent": "ventas",
        "filters": filters,
        "order_by": order_by,
        "limit": limit,
    }

def parse_productos_query(text):
    """
    Parser específico para consultas de productos.
    Soporta consultas como:
    - "Productos más vendidos de este mes"
    - "Los 5 productos menos vendidos"
    - "Productos que generaron más ingresos"
    """
    filters = extract_dates(text)
    limit = extract_limit(text) or 10  # Por defecto 10
    
    # Detectar tipo específico de reporte de productos
    report_type = detect_report_type(text)
    
    return {
        "intent": report_type or "productos",
        "filters": filters,
        "limit": limit,
    }

def parse_ventas_con_producto(text):
    """
    Parser para ventas que incluyen información de productos.
    Ejemplo: "Ventas de este mes con el producto más vendido"
    """
    filters = extract_dates(text)
    
    # Detectar si pide el producto más vendido
    if re.search(r"producto\s+(?:más|mas)\s+vendido", text.lower()):
        filters['incluir_producto_mas_vendido'] = True
    
    return {
        "intent": "ventas_con_producto",
        "filters": filters,
    }

def parse_query(text):
    """
    Parser general de entrada: detecta tipo de reporte y llama al parser correcto.
    Maneja consultas en lenguaje natural español.
    """
    text_lower = text.lower()
    
    # Detectar el tipo de reporte
    report_type = detect_report_type(text)
    
    # Ventas con producto específico
    if report_type == "ventas_con_producto":
        return parse_ventas_con_producto(text)
    
    # Productos (más vendidos, menos vendidos, ingresos, etc.)
    if report_type and report_type.startswith("productos"):
        return parse_productos_query(text)
    
    # Ventas generales
    if report_type and (report_type.startswith("ventas") or "venta" in text_lower):
        result = parse_ventas_query(text)
        # Actualizar el intent con el tipo específico
        if report_type in ["ventas_mayores_a", "ventas_menores_a", "ventas_entre_montos"]:
            result["intent"] = report_type
        return result
    
    # Clientes (mantener compatibilidad)
    if "cliente" in text_lower:
        return {
            "intent": "clientes",
            "filters": extract_dates(text),
            "order_by": "nombre",
            "limit": 20
        }
    
    # Si no se detecta nada, lanzar error
    raise UnknownReportError(text_lower)

