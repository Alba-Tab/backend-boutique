# apps/venta/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Venta
from .serializers import (
    VentaListSerializer,
    VentaDetailSerializer,
    CrearVentaSerializer
)
from .services import VentaService

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    # permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VentaDetailSerializer  # Con detalles
        return VentaListSerializer  # Sin detalles

    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_staff:
    #         return Venta.objects.all().select_related('cliente')
    #     return Venta.objects.filter(cliente=user).select_related('cliente')

    @action(detail=False, methods=['post'])
    def crear(self, request):
        serializer = CrearVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            venta = VentaService.crear_venta(
                cliente_id=serializer.validated_data.get('cliente'),  # ⬅️ Usar .get() en vez de ['cliente']
                items=serializer.validated_data['items'],
                tipo_pago=serializer.validated_data['tipo_pago'],
                interes=serializer.validated_data.get('interes'),
                plazo_meses=serializer.validated_data.get('plazo_meses')
            )

            response_serializer = VentaDetailSerializer(venta)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        """GET /api/ventas/{id}/detalles/"""
        venta = self.get_object()

        from apps.detalle_venta.serializers import DetalleVentaSerializer
        detalles = venta.detalles.all()
        serializer = DetalleVentaSerializer(detalles, many=True)

        return Response(serializer.data)
