from django.urls import path
from .views import (
    ReportQueryView,
    ReportByTypeView,
    dashboard_view,
    cierre_dia_view,
    alertas_inventario_view
)

urlpatterns = [
    # Reporte con lenguaje natural
    path('query/', ReportQueryView.as_view(), name='report-query'),
    
    # Reporte por tipo directo
    path('generate/', ReportByTypeView.as_view(), name='report-generate'),
    
    # Endpoints útiles para frontend
    path('dashboard/', dashboard_view, name='report-dashboard'),
    path('cierre-dia/', cierre_dia_view, name='report-cierre-dia'),
    path('alertas-inventario/', alertas_inventario_view, name='report-alertas'),
]
