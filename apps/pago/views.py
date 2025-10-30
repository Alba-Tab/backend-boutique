from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Pago
from .serializers import PagoSerializer, RegistrarPagoSerializer
from .services import PagoService  # ⬅️ Usar service local


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos

    Endpoints:
    - GET  /api/pagos/              → Lista todos los pagos
    - POST /api/pagos/              → Registrar un pago
    - GET  /api/pagos/{id}/         → Detalle de un pago
    - GET  /api/pagos/por_venta/{venta_id}/ → Pagos de una venta específica
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     """
    #     Filtrar según el usuario:
    #     - Admin ve todos los pagos
    #     - Usuario normal solo ve pagos de sus ventas
    #     """
    #     user = self.request.user

    #     if user.is_staff:
    #         return Pago.objects.all().select_related('venta', 'venta__cliente')

    #     return Pago.objects.filter(
    #         venta__cliente=user
    #     ).select_related('venta')

    def create(self, request, *args, **kwargs):
        """
        POST /api/pagos/

        Body: {
            "venta": 1,
            "monto_pagado": 50000,
            "metodo_pago": "efectivo",
            "referencia_pago": "Pago inicial"
        }
        """
        serializer = RegistrarPagoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Usar el service para registrar el pago
            pago = PagoService.registrar_pago(
                venta_id=serializer.validated_data['venta'],
                monto_pagado=serializer.validated_data['monto_pagado'],
                metodo_pago=serializer.validated_data['metodo_pago'],
                referencia_pago=serializer.validated_data.get('referencia_pago', '')
            )

            # Obtener información actualizada de la venta
            venta = pago.venta
            total_pagado = sum(p.monto_pagado for p in venta.pagos.all())
            total_a_pagar = (
                venta.total_con_interes
                if venta.tipo_pago == 'credito'
                else venta.total
            )

            response_serializer = PagoSerializer(pago)

            return Response({
                'message': 'Pago registrado exitosamente',
                'pago': response_serializer.data,
                'venta': {
                    'id': venta.id,
                    'estado_pago': venta.estado_pago,
                    'total': str(total_a_pagar),
                    'total_pagado': str(total_pagado),
                    'saldo_pendiente': str(total_a_pagar - total_pagado)
                }
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='por_venta/(?P<venta_id>[^/.]+)')
    def por_venta(self, request, venta_id=None):
        """
        GET /api/pagos/por_venta/{venta_id}/

        Retorna todos los pagos de una venta específica
        """
        pagos = self.get_queryset().filter(venta_id=venta_id).order_by('fecha_pago')
        serializer = self.get_serializer(pagos, many=True)

        # Calcular totales
        total_pagado = sum(p.monto_pagado for p in pagos)

        return Response({
            'venta_id': int(venta_id),
            'total_pagado': str(total_pagado),
            'cantidad_pagos': pagos.count(),
            'pagos': serializer.data
        })
