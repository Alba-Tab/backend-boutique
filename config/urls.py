
from unittest.mock import patch
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("apps.usuarios.urls")),
    path('api/', include("apps.productos.urls")),
    path('api/', include("apps.categorias.urls")),
    path('api/', include("apps.producto_variante.urls")),
    path('api/', include("apps.venta.urls")),
    path('api/', include("apps.pago.urls")),
    path('api/', include("apps.cuota.urls")),
    path('api/reports/', include("apps.reports.urls")),
]
