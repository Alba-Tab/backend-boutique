# apps/venta/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.pago.services import PagoService
from apps.pago.serializers import PagoSerializer, PagoAlContadoSerializer
from .models import Venta
from .serializers import (
    VentaListSerializer,
    VentaDetailSerializer,
    CrearVentaSerializer,
    DetalleVentaSerializer
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
                cliente_id=serializer.validated_data.get('cliente'),
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
        detalles = venta.detalles.all()
        serializer = DetalleVentaSerializer(detalles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pagar_al_contado(self, request, pk=None):
        venta = self.get_object()
        
        if venta.tipo_pago != 'contado':
            return Response(
                {'error': 'Esta venta no es al contado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PagoAlContadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            pago = PagoService.registrar_pago_al_contado(
                venta_id=venta.id,
                metodo_pago=serializer.validated_data['metodo_pago'],
                referencia_pago=serializer.validated_data.get('referencia_pago')
            )
            
            pago_serializer = PagoSerializer(pago)
            venta_serializer = VentaDetailSerializer(venta)
            
            return Response({
                'message': 'Venta pagada completamente',
                'pago': pago_serializer.data,
                'venta': venta_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def agregar_detalle(self, request, pk=None):
        """POST /api/ventas/{id}/agregar_detalle/
        """
        venta = self.get_object()
        
        serializer = DetalleVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        detalle = serializer.save(venta=venta)
        
        venta.calcular_total()
        
        return Response(
            DetalleVentaSerializer(detalle).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'])
    def actualizar_detalle(self, request, pk=None):
        """PATCH /api/ventas/{id}/actualizar_detalle/?detalle_id=X
        """
        venta = self.get_object()
        detalle_id = request.query_params.get('detalle_id')
        
        if not detalle_id:
            return Response(
                {'error': 'detalle_id es requerido como query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            detalle = venta.detalles.get(id=detalle_id)
            
            serializer = DetalleVentaSerializer(detalle, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Recalcular total
            venta.calcular_total()
            
            return Response(DetalleVentaSerializer(detalle).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def eliminar_detalle(self, request, pk=None):
        """DELETE /api/ventas/{id}/eliminar_detalle/?detalle_id=X
        Elimina un detalle específico de la venta
        """
        venta = self.get_object()
        detalle_id = request.query_params.get('detalle_id')
        
        if not detalle_id:
            return Response(
                {'error': 'detalle_id es requerido como query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            detalle = venta.detalles.get(id=detalle_id)
            detalle.delete()
            
            # Recalcular total
            venta.calcular_total()
            
            return Response(
                {'message': 'Detalle eliminado correctamente'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    # @action(detail=True, methods=['get'])
    # def detalles(self, request, pk=None):
    #     """GET /api/ventas/{id}/detalles/"""
    #     venta = self.get_object()

    #     detalles = venta.detalles.all()
    #     serializer = VentaDetailSerializer(detalles, many=True)

    #     return Response(serializer.data)
