from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from .models import VarianteProducto
from .serializers import VarianteProductoSerializer

class VarianteProductoViewSet(viewsets.ModelViewSet):
    queryset = VarianteProducto.objects.all()
    serializer_class = VarianteProductoSerializer
