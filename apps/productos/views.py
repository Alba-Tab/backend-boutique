from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Producto
from .serializers import ProductoSerializer
from apps.producto_variante.serializers import VarianteProductoSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['categoria', 'marca', 'genero']

    def get_queryset(self):
        """
        Sobreescribe queryset para filtrar por características de variantes
        """
        queryset = super().get_queryset()

        # Filtro por talla de variante
        talla = self.request.query_params.get('talla')
        if talla:
            queryset = queryset.filter(variantes__talla=talla).distinct()

        # Filtro por precio mínimo
        precio_min = self.request.query_params.get('precio_min')
        if precio_min:
            queryset = queryset.filter(variantes__precio__gte=precio_min).distinct()

        # Filtro por precio máximo
        precio_max = self.request.query_params.get('precio_max')
        if precio_max:
            queryset = queryset.filter(variantes__precio__lte=precio_max).distinct()

        # Filtro por stock disponible
        en_stock = self.request.query_params.get('en_stock')
        if en_stock == 'true':
            queryset = queryset.filter(variantes__stock__gt=0).distinct()

        return queryset

    @action(detail=True, methods=['get'])
    def variantes(self, request, pk=None):
        """
        GET /api/productos/{id}/variantes/
        Retorna todas las variantes del producto

        Query params opcionales:
        - talla: filtrar por talla
        - en_stock: true/false para filtrar con stock disponible
        """
        producto = self.get_object()
        variantes = producto.variantes.all()

        # Filtros opcionales
        talla = request.query_params.get('talla')
        if talla:
            variantes = variantes.filter(talla=talla)

        en_stock = request.query_params.get('en_stock')
        if en_stock == 'true':
            variantes = variantes.filter(stock__gt=0)

        serializer = VarianteProductoSerializer(variantes, many=True)
        return Response(serializer.data)
