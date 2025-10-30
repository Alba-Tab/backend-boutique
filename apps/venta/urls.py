# apps/venta/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VentaViewSet

router = DefaultRouter()
router.register(r'ventas', VentaViewSet, basename='venta')

urlpatterns = [
    path('', include(router.urls)),
]
