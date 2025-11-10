from django.urls import path
from .views import (
    GenerateReportView,
    dashboard_view,
    productos_mas_vendidos_view,
    ventas_por_categoria_view,
    clientes_frecuentes_view,
    inventario_critico_view,
    estado_creditos_view
)

urlpatterns = [
    # Generar reporte y enviarlo por correo via n8n
    path('generate/', GenerateReportView.as_view(), name='report-generate'),
    
    # Dashboard principal con todos los datos
    path('dashboard/', dashboard_view, name='report-dashboard'),
    
    # Reportes específicos para boutique de ropa
    path('productos-mas-vendidos/', productos_mas_vendidos_view, name='productos-mas-vendidos'),
    path('ventas-por-categoria/', ventas_por_categoria_view, name='ventas-por-categoria'),
    path('clientes-frecuentes/', clientes_frecuentes_view, name='clientes-frecuentes'),
    path('inventario-critico/', inventario_critico_view, name='inventario-critico'),
    path('estado-creditos/', estado_creditos_view, name='estado-creditos'),
]
