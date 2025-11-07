from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import VarianteProducto
from .serializers import VarianteProductoSerializer

class VarianteProductoViewSet(viewsets.ModelViewSet):
    queryset = VarianteProducto.objects.select_related('producto').all()
    serializer_class = VarianteProductoSerializer

    @action(detail=False, methods=['get'])
    def sin_stock(self, request):
        """Obtener variantes sin stock"""
        variantes = self.queryset.filter(stock=0)
        serializer = self.get_serializer(variantes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """Obtener variantes con stock bajo (menor o igual al mínimo)"""
        from django.db.models import F
        variantes = self.queryset.filter(stock__lte=F('stock_minimo'))
        serializer = self.get_serializer(variantes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def ajustar_stock(self, request, pk=None):
        """Ajustar stock de una variante (suma o resta)"""
        variante = self.get_object()
        cantidad = request.data.get('cantidad', 0)

        try:
            cantidad = int(cantidad)
            nuevo_stock = variante.stock + cantidad

            if nuevo_stock < 0:
                return Response(
                    {'error': 'No hay suficiente stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            variante.stock = nuevo_stock
            variante.save()

            serializer = self.get_serializer(variante)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Cantidad inválida'},
                status=status.HTTP_400_BAD_REQUEST
            )
