from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Pago
from .serializers import PagoSerializer, RegistrarPagoSerializer, PagoAlContadoSerializer
from .services import PagoService


class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos

    Endpoints:
    - GET  /api/pagos/                          → Lista todos los pagos
    - POST /api/pagos/                          → Registrar un pago
    - GET  /api/pagos/{id}/                     → Detalle de un pago
    - GET  /api/pagos/por_venta/{venta_id}/     → Pagos de una venta específica
    - POST /api/pagos/pagar_cuota/              → Pagar una cuota específica
    - POST /api/ventas/{id}/pagar_al_contado/   → Pagar venta al contado (desde VentaViewSet)
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    # permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        POST /api/pagos/

        Body: {
            "venta": 1,
            "monto_pagado": 500.00,
            "metodo_pago": "efectivo",
            "cuota": 1,  // Opcional - para pagar cuota específica
            "referencia_pago": "Pago parcial"
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
                referencia_pago=serializer.validated_data.get('referencia_pago', ''),
                cuota_id=serializer.validated_data.get('cuota')
            )

            # Obtener información actualizada de la venta
            venta = pago.venta
            total_pagado = sum(p.monto_pagado for p in venta.pagos.all())
            total_a_pagar = (
                venta.total_con_interes
                if venta.tipo_venta == 'credito' and venta.total_con_interes
                else venta.total
            )

            response_serializer = PagoSerializer(pago)

            return Response({
                'message': 'Pago registrado exitosamente',
                'pago': response_serializer.data,
                'venta': {
                    'id': venta.id,
                    'estado': venta.estado,
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

    @action(detail=False, methods=['post'])
    def pagar_cuota(self, request):
        """
        POST /api/pagos/pagar_cuota/

        Body: {
            "venta": 1,
            "cuota": 2,
            "metodo_pago": "efectivo",
            "referencia_pago": "Pago cuota 2"
        }
        """
        cuota_id = request.data.get('cuota')
        if not cuota_id:
            return Response(
                {'error': 'El campo "cuota" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la cuota para saber el monto
        from apps.cuota.models import CuotaCredito
        try:
            cuota = CuotaCredito.objects.get(id=cuota_id)
            monto = cuota.monto_cuota
        except CuotaCredito.DoesNotExist:
            return Response(
                {'error': 'Cuota no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear payload con el monto de la cuota
        data = request.data.copy()
        data['monto_pagado'] = monto
        data['venta'] = cuota.venta.id

        serializer = RegistrarPagoSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            pago = PagoService.registrar_pago(
                venta_id=serializer.validated_data['venta'],
                monto_pagado=serializer.validated_data['monto_pagado'],
                metodo_pago=serializer.validated_data['metodo_pago'],
                referencia_pago=serializer.validated_data.get('referencia_pago', ''),
                cuota_id=cuota_id
            )

            response_serializer = PagoSerializer(pago)

            return Response({
                'message': f'Cuota {cuota.numero_cuota} pagada exitosamente',
                'pago': response_serializer.data
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
