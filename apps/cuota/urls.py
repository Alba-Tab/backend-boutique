from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuotaViewSet

router = DefaultRouter()
router.register(r'cuotas', CuotaViewSet, basename='cuota')

urlpatterns = [
    path('', include(router.urls)),
]
