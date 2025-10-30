from email.mime import base
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.producto_variante.views import VarianteProductoViewSet


router = DefaultRouter()
router.register(r'producto-variante', VarianteProductoViewSet, basename='producto-variante')

urlpatterns = [
    path('', include(router.urls)),
]
