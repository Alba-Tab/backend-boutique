
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("apps.usuarios.urls")),
    path('api/', include("apps.productos.urls")),
    path('api/', include("apps.categorias.urls")),
]
