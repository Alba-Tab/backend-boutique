from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .serializers import ReportQueryInputSerializer, ReportQueryOutputSerializer
from .services.report_generator import generate_report, generate_report_by_type
from .services import ventas_report_service, products_report_service, pagos_report_service
from datetime import datetime, timedelta


class ReportQueryView(APIView):
    """
    POST /api/v1/reports/query/
    body: {"query": "reporte de ventas del 1 al 15 de octubre ordenado por monto"}
    
    Genera reportes usando lenguaje natural
    """

    def post(self, request):
        serializer_in = ReportQueryInputSerializer(data=request.data)
        serializer_in.is_valid(raise_exception=True)

        query_text = serializer_in.validated_data["query"]
        try:
            result = generate_report(query_text)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer_out = ReportQueryOutputSerializer(result)
        return Response(serializer_out.data, status=status.HTTP_200_OK)


class ReportByTypeView(APIView):
    """
    POST /api/v1/reports/generate/
    body: {
        "report_type": "ventas",
        "filters": {
            "fecha_inicio": "2025-01-01",
            "fecha_fin": "2025-01-31"
        }
    }
    
    Genera reportes directamente por tipo
    
    Tipos disponibles:
    - ventas, ventas_cliente, ventas_periodo
    - productos, stock_bajo, mas_vendidos, sin_ventas, rentabilidad
    - pagos, cuotas, morosidad, flujo_caja
    """

    def post(self, request):
        report_type = request.data.get('report_type')
        filters = request.data.get('filters', {})
        
        if not report_type:
            return Response(
                {
                    "error": "report_type es requerido",
                    "tipos_disponibles": [
                        "ventas", "ventas_cliente", "ventas_periodo",
                        "productos", "stock_bajo", "mas_vendidos", "sin_ventas", "rentabilidad",
                        "pagos", "cuotas", "morosidad", "flujo_caja"
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            resultado = generate_report_by_type(report_type, filters)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def dashboard_view(request):
    """
    GET /api/v1/reports/dashboard/
    
    Retorna datos para el dashboard administrativo:
    - Ventas del mes
    - Top 5 productos más vendidos
    - Stock crítico
    - Morosidad
    - Flujo de caja del mes
    """
    try:
        hoy = datetime.now().date()
        hace_30_dias = hoy - timedelta(days=30)
        
        dashboard_data = {
            # Ventas del mes
            "ventas_mes": ventas_report_service.report_ventas({
                'fecha_inicio': str(hace_30_dias),
                'fecha_fin': str(hoy)
            }),
            
            # Top 5 productos más vendidos
            "top_productos": products_report_service.report_productos_mas_vendidos(5),
            
            # Stock crítico
            "stock_critico": products_report_service.report_stock_bajo(),
            
            # Morosidad
            "morosidad": pagos_report_service.report_morosidad(),
            
            # Flujo de caja del mes
            "flujo_caja": pagos_report_service.report_flujo_caja({
                'fecha_inicio': str(hace_30_dias),
                'fecha_fin': str(hoy)
            })
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def cierre_dia_view(request):
    """
    GET /api/v1/reports/cierre-dia/
    
    Reporte de cierre diario para caja:
    - Ventas del día
    - Pagos recibidos por método
    - Total recaudado
    """
    try:
        hoy = datetime.now().date()
        
        # Ventas del día
        ventas = ventas_report_service.report_ventas({
            'fecha_inicio': str(hoy),
            'fecha_fin': str(hoy)
        })
        
        # Pagos recibidos
        pagos = pagos_report_service.report_pagos({
            'fecha_inicio': str(hoy),
            'fecha_fin': str(hoy)
        })
        
        # Buscar montos por método
        ingresos_efectivo = next(
            (p['monto_total'] for p in pagos['rows'] if p['método_pago'] == 'efectivo'),
            0
        )
        ingresos_tarjeta = next(
            (p['monto_total'] for p in pagos['rows'] if p['método_pago'] == 'tarjeta'),
            0
        )
        ingresos_qr = next(
            (p['monto_total'] for p in pagos['rows'] if p['método_pago'] == 'qr'),
            0
        )
        
        cierre = {
            "fecha": str(hoy),
            "ventas": {
                "cantidad": ventas['meta']['cantidad_ventas'],
                "total": ventas['meta']['total_ventas'],
                "promedio": ventas['meta']['promedio_venta']
            },
            "ingresos": {
                "efectivo": ingresos_efectivo,
                "tarjeta": ingresos_tarjeta,
                "qr": ingresos_qr,
                "total": pagos['meta']['total_pagos']
            },
            "detalle_ventas": ventas['rows'],
            "detalle_pagos": pagos['rows']
        }
        
        return Response(cierre, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def alertas_inventario_view(request):
    """
    GET /api/v1/reports/alertas-inventario/
    
    Alertas de productos que necesitan atención:
    - Productos sin stock (CRÍTICO)
    - Productos con stock bajo
    - Productos sin movimiento (últimos 90 días)
    """
    try:
        stock_bajo = products_report_service.report_stock_bajo()
        sin_ventas = products_report_service.report_productos_sin_ventas()
        
        alertas = {
            "urgente": [
                p for p in stock_bajo['rows'] 
                if p['estado'] == 'CRÍTICO'
            ],
            "bajo_stock": [
                p for p in stock_bajo['rows'] 
                if p['estado'] == 'BAJO'
            ],
            "sin_movimiento": sin_ventas['rows'][:10],  # Top 10
            "resumen": {
                "productos_criticos": stock_bajo['meta']['sin_stock'],
                "productos_bajo_stock": stock_bajo['meta']['total_productos_criticos'] - stock_bajo['meta']['sin_stock'],
                "productos_sin_ventas": sin_ventas['meta']['total_productos']
            }
        }
        
        return Response(alertas, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )