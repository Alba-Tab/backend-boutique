from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.db.models import Sum, Count, Avg, F, Q, DecimalField, Case, When, Value, CharField, Max
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from datetime import datetime, timedelta
from decimal import Decimal
import requests

from apps.venta.models import Venta, DetalleVenta
from apps.productos.models import Producto
from apps.producto_variante.models import VarianteProducto
from apps.pago.models import Pago
from apps.cuota.models import CuotaCredito
from apps.usuarios.models import Usuario


class GenerateReportView(APIView):
    """
    POST /api/reports/generate/
    body: {
        "query": "Genera un reporte de las ventas del último mes" (requerido),
        "user_email": "usuario@ejemplo.com" (opcional, por defecto garcia.brayan3001@gmail.com)
    }
    
    Genera un reporte usando lenguaje natural y lo envía al correo especificado mediante n8n
    """

    def post(self, request):
        query = request.data.get('query')
        user_email = request.data.get('user_email', 'garcia.brayan3001@gmail.com')
        
        # Validar que se envió la query
        if not query:
            return Response(
                {
                    "error": "El campo 'query' es requerido",
                    "details": "Debes proporcionar una consulta en lenguaje natural"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Llamar a la URL de n8n para generar el reporte
            response = requests.post(
                'https://albatab.app.n8n.cloud/webhook/report/nlp',
                json={
                    'query': query,
                    'email': user_email
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return Response(
                    {
                        "message": f"Reporte enviado exitosamente a {user_email}",
                        "status": "success"
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "error": "Error al generar el reporte",
                        "details": response.text
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Error de conexión: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def dashboard_view(request):
    """
    GET /api/v1/reports/dashboard/
    
    Retorna datos completos para el dashboard administrativo
    """
    try:
        hoy = datetime.now().date()
        hace_7_dias = hoy - timedelta(days=7)
        hace_30_dias = hoy - timedelta(days=30)
        
        # 1. Ventas del mes con evolución semanal
        ventas_mes_data = Venta.objects.filter(
            fecha__gte=hace_30_dias,
            fecha__lte=hoy
        ).aggregate(
            total=Sum('total'),
            cantidad=Count('id')
        )
        
        # Calcular el promedio manualmente
        ventas_mes = {
            'total': ventas_mes_data['total'] or 0,
            'cantidad': ventas_mes_data['cantidad'] or 0,
            'promedio': (ventas_mes_data['total'] / ventas_mes_data['cantidad']) if ventas_mes_data['cantidad'] and ventas_mes_data['cantidad'] > 0 else 0
        }
        
        # Ventas por día de la última semana
        ventas_semana = Venta.objects.filter(
            fecha__gte=hace_7_dias
        ).annotate(
            dia=TruncDay('fecha')
        ).values('dia').annotate(
            total=Sum('total')
        ).order_by('dia')
        
        # 2. Top 5 productos más vendidos
        productos_vendidos = DetalleVenta.objects.filter(
            venta__fecha__gte=hace_30_dias
        ).values(
            'nombre_producto',
            'variante_producto__producto__image'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos=Sum('sub_total')
        ).order_by('-cantidad_vendida')[:5]
        
        # 3. Top 5 clientes que más compran
        top_clientes = Venta.objects.filter(
            fecha__gte=hace_30_dias,
            cliente__isnull=False
        ).values(
            'nombre_cliente',
            'correo_cliente',
            'numero_cliente'
        ).annotate(
            total_compras=Sum('total'),
            cantidad_compras=Count('id')
        ).order_by('-total_compras')[:5]
        
        # 4. Stock crítico (productos con stock bajo o agotado)
        stock_critico = VarianteProducto.objects.filter(
            Q(stock__lte=F('stock_minimo')) | Q(stock=0)
        ).select_related('producto').annotate(
            estado=Case(
                When(stock=0, then=Value('AGOTADO')),
                default=Value('BAJO'),
                output_field=CharField()
            )
        ).values(
            'producto__nombre',
            'talla',
            'stock',
            'stock_minimo',
            'estado'
        ).order_by('stock')[:10]
        
        # 5. Ingresos por método de pago (últimos 30 días)
        ingresos_metodo = Pago.objects.filter(
            fecha_pago__gte=hace_30_dias
        ).values('metodo_pago').annotate(
            total=Sum('monto_pagado'),
            cantidad=Count('id')
        )
        
        # 6. Morosidad - Cuotas vencidas
        cuotas_vencidas = CuotaCredito.objects.filter(
            estado='vencida'
        ).aggregate(
            total_monto=Sum('monto_cuota'),
            cantidad=Count('id')
        )
        
        cuotas_pendientes = CuotaCredito.objects.filter(
            estado='pendiente'
        ).aggregate(
            total_monto=Sum('monto_cuota'),
            cantidad=Count('id')
        )
        
        # 7. Ventas por tipo (contado vs crédito)
        ventas_por_tipo = Venta.objects.filter(
            fecha__gte=hace_30_dias
        ).values('tipo_venta').annotate(
            total=Sum('total'),
            cantidad=Count('id')
        )
        
        # 8. Productos sin ventas en los últimos 30 días
        productos_vendidos_ids = DetalleVenta.objects.filter(
            venta__fecha__gte=hace_30_dias
        ).values_list('variante_producto__producto_id', flat=True).distinct()
        
        productos_sin_movimiento = Producto.objects.exclude(
            id__in=productos_vendidos_ids
        ).count()
        
        # 9. Ingresos por día de la semana
        ingresos_diarios = Pago.objects.filter(
            fecha_pago__date__gte=hace_7_dias
        ).annotate(
            dia=TruncDay('fecha_pago')
        ).values('dia').annotate(
            total=Sum('monto_pagado')
        ).order_by('dia')
        
        # Construir respuesta estructurada
        dashboard_data = {
            # Resumen general
            "resumen": {
                "ventas_mes": {
                    "total": float(ventas_mes['total'] or 0),
                    "cantidad": ventas_mes['cantidad'] or 0,
                    "promedio": float(ventas_mes['promedio'] or 0)
                },
                "morosidad": {
                    "cuotas_vencidas": cuotas_vencidas['cantidad'] or 0,
                    "monto_vencido": float(cuotas_vencidas['total_monto'] or 0),
                    "cuotas_pendientes": cuotas_pendientes['cantidad'] or 0,
                    "monto_pendiente": float(cuotas_pendientes['total_monto'] or 0)
                },
                "productos_sin_movimiento": productos_sin_movimiento,
                "productos_stock_critico": len(list(stock_critico))
            },
            
            # Para gráfico de ventas (ProductSales)
            "ventas_semana": [
                {
                    "fecha": v['dia'].strftime('%Y-%m-%d'),
                    "total": float(v['total'])
                }
                for v in ventas_semana
            ],
            
            # Para gráfico de profit/expenses
            "ingresos_diarios": [
                {
                    "fecha": i['dia'].strftime('%Y-%m-%d'),
                    "total": float(i['total'])
                }
                for i in ingresos_diarios
            ],
            
            # Top productos más vendidos
            "top_productos": [
                {
                    "nombre": p['nombre_producto'],
                    "cantidad_vendida": p['cantidad_vendida'],
                    "ingresos": float(p['ingresos']),
                    "imagen": str(p['variante_producto__producto__image']) if p['variante_producto__producto__image'] else None
                }
                for p in productos_vendidos
            ],
            
            # Top clientes (TopPayingClients)
            "top_clientes": [
                {
                    "nombre": c['nombre_cliente'] or 'Cliente sin nombre',
                    "correo": c['correo_cliente'] or 'sin@correo.com',
                    "telefono": c['numero_cliente'] or 'N/A',
                    "total_compras": float(c['total_compras']),
                    "cantidad_compras": c['cantidad_compras']
                }
                for c in top_clientes
            ],
            
            # Stock crítico
            "stock_critico": [
                {
                    "producto": s['producto__nombre'],
                    "talla": s['talla'],
                    "stock_actual": s['stock'],
                    "stock_minimo": s['stock_minimo'],
                    "estado": s['estado']
                }
                for s in stock_critico
            ],
            
            # Ingresos por método de pago
            "ingresos_metodo": [
                {
                    "metodo": m['metodo_pago'],
                    "total": float(m['total']),
                    "cantidad_transacciones": m['cantidad']
                }
                for m in ingresos_metodo
            ],
            
            # Ventas por tipo
            "ventas_tipo": [
                {
                    "tipo": v['tipo_venta'],
                    "total": float(v['total']),
                    "cantidad": v['cantidad']
                }
                for v in ventas_por_tipo
            ]
        }
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        import traceback
        return Response(
            {
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def productos_mas_vendidos_view(request):
    """
    GET /api/v1/reports/productos-mas-vendidos/
    
    Productos más vendidos con detalles
    """
    try:
        dias = int(request.query_params.get('dias', 30))
        limite = int(request.query_params.get('limite', 10))
        
        fecha_inicio = datetime.now().date() - timedelta(days=dias)
        
        productos = DetalleVenta.objects.filter(
            venta__fecha__gte=fecha_inicio
        ).values(
            'variante_producto__producto__id',
            'variante_producto__producto__nombre',
            'variante_producto__producto__categoria__nombre',
            'variante_producto__producto__marca',
            'talla'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            ingresos_totales=Sum('sub_total'),
            numero_ventas=Count('venta', distinct=True)
        ).order_by('-cantidad_vendida')[:limite]
        
        return Response({
            "periodo": f"Últimos {dias} días",
            "productos": list(productos)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def ventas_por_categoria_view(request):
    """
    GET /api/v1/reports/ventas-por-categoria/
    
    Distribución de ventas por categoría de productos
    """
    try:
        dias = int(request.query_params.get('dias', 30))
        fecha_inicio = datetime.now().date() - timedelta(days=dias)
        
        categorias = DetalleVenta.objects.filter(
            venta__fecha__gte=fecha_inicio
        ).values(
            'variante_producto__producto__categoria__nombre'
        ).annotate(
            total_ventas=Sum('sub_total'),
            cantidad_productos=Sum('cantidad'),
            numero_transacciones=Count('venta', distinct=True)
        ).order_by('-total_ventas')
        
        return Response({
            "periodo": f"Últimos {dias} días",
            "categorias": list(categorias)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def clientes_frecuentes_view(request):
    """
    GET /api/v1/reports/clientes-frecuentes/
    
    Clientes que más compran (frecuencia y monto)
    """
    try:
        dias = int(request.query_params.get('dias', 90))
        limite = int(request.query_params.get('limite', 10))
        
        fecha_inicio = datetime.now().date() - timedelta(days=dias)
        
        clientes = Venta.objects.filter(
            fecha__gte=fecha_inicio,
            cliente__isnull=False
        ).values(
            'cliente__id',
            'cliente__nombre',
            'cliente__correo',
            'cliente__numero'
        ).annotate(
            total_gastado=Sum('total'),
            cantidad_compras=Count('id'),
            ticket_promedio=Avg('total'),
            ultima_compra=Max('fecha')
        ).order_by('-total_gastado')[:limite]
        
        return Response({
            "periodo": f"Últimos {dias} días",
            "clientes": list(clientes)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def inventario_critico_view(request):
    """
    GET /api/v1/reports/inventario-critico/
    
    Productos con stock bajo o agotado
    """
    try:
        productos = VarianteProducto.objects.filter(
            Q(stock__lte=F('stock_minimo')) | Q(stock=0)
        ).select_related('producto', 'producto__categoria').annotate(
            estado=Case(
                When(stock=0, then=Value('AGOTADO')),
                When(stock__lte=F('stock_minimo'), then=Value('BAJO')),
                default=Value('OK'),
                output_field=CharField()
            )
        ).values(
            'id',
            'producto__nombre',
            'producto__categoria__nombre',
            'talla',
            'stock',
            'stock_minimo',
            'precio',
            'estado'
        ).order_by('stock', 'producto__nombre')
        
        productos_list = list(productos)
        agotados = [p for p in productos_list if p['estado'] == 'AGOTADO']
        bajo_stock = [p for p in productos_list if p['estado'] == 'BAJO']
        
        return Response({
            "resumen": {
                "total_criticos": len(productos_list),
                "agotados": len(agotados),
                "bajo_stock": len(bajo_stock)
            },
            "productos_agotados": agotados,
            "productos_bajo_stock": bajo_stock
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def estado_creditos_view(request):
    """
    GET /api/v1/reports/estado-creditos/
    
    Estado de créditos y morosidad
    """
    try:
        # Cuotas por estado
        resumen_cuotas = CuotaCredito.objects.values('estado').annotate(
            cantidad=Count('id'),
            monto_total=Sum('monto_cuota')
        )
        
        # Clientes con cuotas vencidas
        clientes_morosos = CuotaCredito.objects.filter(
            estado='vencida'
        ).values(
            'venta__cliente__nombre',
            'venta__cliente__correo',
            'venta__cliente__numero'
        ).annotate(
            cuotas_vencidas=Count('id'),
            monto_adeudado=Sum('monto_cuota'),
            venta_id=F('venta__id')
        ).order_by('-monto_adeudado')
        
        # Total por recuperar
        total_por_recuperar = CuotaCredito.objects.filter(
            estado__in=['pendiente', 'vencida']
        ).aggregate(
            total=Sum('monto_cuota')
        )
        
        return Response({
            "resumen": list(resumen_cuotas),
            "total_por_recuperar": float(total_por_recuperar['total'] or 0),
            "clientes_morosos": list(clientes_morosos)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )