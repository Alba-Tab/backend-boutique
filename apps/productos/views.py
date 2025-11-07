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

    @action(detail=True, methods=['get'])
    def variantes(self, request, pk=None):
        """
        GET /api/productos/{id}/variantes/
        Retorna todas las variantes del producto

        Query params opcionales:
        - color: filtrar por color
        - talla: filtrar por talla
        - en_stock: true/false para filtrar con stock disponible
        """
        producto = self.get_object()
        variantes = producto.variantes.all()

        # Filtros opcionales
        color = request.query_params.get('color')
        if color:
            variantes = variantes.filter(color=color)

        talla = request.query_params.get('talla')
        if talla:
            variantes = variantes.filter(talla=talla)

        en_stock = request.query_params.get('en_stock')
        if en_stock == 'true':
            variantes = variantes.filter(stock__gt=0)

        serializer = VarianteProductoSerializer(variantes, many=True)
        return Response(serializer.data)
