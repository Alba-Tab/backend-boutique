"""
Configuración de patrones y constantes para el parser de lenguaje natural.
"""

from enum import Enum
from typing import Dict, Any

class ReportIntent(str, Enum):
    """Tipos de intents reconocidos por el sistema."""
    # Ventas
    VENTAS = "ventas"
    VENTAS_MAYORES_A = "ventas_mayores_a"
    VENTAS_MENORES_A = "ventas_menores_a"
    VENTAS_ENTRE_MONTOS = "ventas_entre_montos"
    VENTAS_CON_PRODUCTO = "ventas_con_producto"
    VENTAS_CLIENTE = "ventas_cliente"
    VENTAS_PERIODO = "ventas_periodo"
    
    # Productos
    PRODUCTOS = "productos"
    PRODUCTOS_MAS_VENDIDOS = "productos_mas_vendidos"
    PRODUCTOS_MENOS_VENDIDOS = "productos_menos_vendidos"
    PRODUCTOS_MAS_INGRESOS = "productos_mas_ingresos"
    PRODUCTOS_MENOS_INGRESOS = "productos_menos_ingresos"
    STOCK_BAJO = "stock_bajo"
    SIN_VENTAS = "sin_ventas"
    RENTABILIDAD = "rentabilidad"
    
    # Pagos y cuotas
    PAGOS = "pagos"
    CUOTAS = "cuotas"
    MOROSIDAD = "morosidad"
    FLUJO_CAJA = "flujo_caja"
    
    # Clientes
    CLIENTES = "clientes"



PATTERNS = {
    # Patrones de fechas
    'FECHA': {
        'este_mes': r'este\s+mes|mes\s+actual|del\s+mes',
        'mes_anterior': r'mes\s+anterior|mes\s+pasado|del\s+anterior\s+mes',
        'ultimos_dias': r'(?:últimos|ultimos)\s+(\d+)\s+(?:días|dias)',
        'ultima_semana': r'última\s+semana|ultima\s+semana|semana\s+pasada',
        'rango_especifico': r'(\d{1,2})\s*(?:al|hasta)\s*(\d{1,2})\s*de\s*(\w+)'
    },
    
    # Patrones de montos
    'MONTO': {
        'mayor_a': r'mayor(?:es)?\s+(?:a|que)\s+(\d+(?:\.\d+)?)',
        'menor_a': r'menor(?:es)?\s+(?:a|que)\s+(\d+(?:\.\d+)?)',
        'entre': r'entre\s+(\d+(?:\.\d+)?)\s+y\s+(\d+(?:\.\d+)?)'
    },
    
    # Patrones de cantidad
    'CANTIDAD': {
        'mayor_a': r'cantidad\s+vendida.*mayor(?:es)?\s+(?:a|que)\s+(\d+)',
        'menor_a': r'cantidad\s+vendida.*menor(?:es)?\s+(?:a|que)\s+(\d+)'
    },
    
    # Patrones de límites
    'LIMITE': {
        'top_n': r'(?:top|los|primeros?)\s+(\d+)',
        'numeros_texto': {
            'cinco': 5, 'diez': 10, 'quince': 15, 'veinte': 20,
            'treinta': 30, 'cincuenta': 50, 'cien': 100
        }
    },
    
    # Patrones de ordenamiento
    'ORDEN': {
        'descendente': r'mayor(?:es)?\s+(?:a|primero)|descendente|de\s+mayor\s+a\s+menor',
        'ascendente': r'menor(?:es)?\s+(?:a|primero)|ascendente|de\s+menor\s+a\s+mayor'
    }
}

INTENT_KEYWORDS = {
    ReportIntent.PRODUCTOS_MAS_VENDIDOS: [
        r'productos?\s+(?:más|mas)\s+vendidos?'
    ],
    ReportIntent.PRODUCTOS_MENOS_VENDIDOS: [
        r'productos?\s+menos\s+vendidos?'
    ],
    ReportIntent.PRODUCTOS_MAS_INGRESOS: [
        r'productos?.*(?:más|mas).*ingresos?',
        r'productos?.*(?:más|mas).*rentabl'
    ],
    ReportIntent.PRODUCTOS_MENOS_INGRESOS: [
        r'productos?.*menos.*ingresos?',
        r'productos?.*menos.*rentabl'
    ],
    ReportIntent.VENTAS_CON_PRODUCTO: [
        r'ventas?.*(?:con|del)\s+producto'
    ],
    ReportIntent.PRODUCTOS: [
        r'producto'
    ],
    ReportIntent.VENTAS: [
        r'venta'
    ],
    ReportIntent.CLIENTES: [
        r'cliente'
    ]
}

DEFAULTS: Dict[str, Any] = {
    'limite_productos': 10,
    'limite_ventas': 50,
    'orden_default': '-fecha',
    'monto_min_default': 0,
    'monto_max_default': 10000
}
