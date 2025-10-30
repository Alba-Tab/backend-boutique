from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import CuotaCredito
from .serializers import CuotaSerializer, MarcarCuotaPagadaSerializer


class CuotaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar cuotas de crédito

    Endpoints:
    - GET /api/cuotas/                    → Lista todas las cuotas
    - GET /api/cuotas/{id}/               → Detalle de una cuota
    - GET /api/cuotas/vencidas/           → Cuotas vencidas
    - GET /api/cuotas/proximas_vencer/    → Cuotas próximas a vencer
    - POST /api/cuotas/{id}/marcar_pagada/ → Marcar cuota como pagada
    """
    queryset = CuotaCredito.objects.all()
    serializer_class = CuotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtrar según el usuario:
        - Admin ve todas las cuotas
        - Usuario normal solo ve sus cuotas
        """
        user = self.request.user

        if user.is_staff:
            return CuotaCredito.objects.all().select_related(
                'venta',
                'venta__cliente'
            ).order_by('fecha_vencimiento')

        return CuotaCredito.objects.filter(
            venta__cliente=user
        ).select_related('venta').order_by('fecha_vencimiento')

    @action(detail=False, methods=['get'])
    def vencidas(self, request):
        """
        GET /api/cuotas/vencidas/

        Retorna todas las cuotas vencidas
        """
        cuotas = self.get_queryset().filter(estado='vencida')
        serializer = self.get_serializer(cuotas, many=True)

        return Response({
            'count': cuotas.count(),
            'cuotas': serializer.data
        })

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        GET /api/cuotas/pendientes/

        Retorna todas las cuotas pendientes
        """
        cuotas = self.get_queryset().filter(estado='pendiente')
        serializer = self.get_serializer(cuotas, many=True)

        return Response({
            'count': cuotas.count(),
            'cuotas': serializer.data
        })

    @action(detail=False, methods=['get'])
    def proximas_vencer(self, request):
        """
        GET /api/cuotas/proximas_vencer/?dias=7

        Retorna cuotas que vencen en los próximos N días
        """
        dias = int(request.query_params.get('dias', 7))
        fecha_hoy = timezone.now().date()
        fecha_limite = fecha_hoy + timezone.timedelta(days=dias)

        cuotas = self.get_queryset().filter(
            estado='pendiente',
            fecha_vencimiento__range=[fecha_hoy, fecha_limite]
        )

        serializer = self.get_serializer(cuotas, many=True)

        return Response({
            'count': cuotas.count(),
            'dias': dias,
            'cuotas': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def marcar_pagada(self, request, pk=None):
        """
        POST /api/cuotas/{id}/marcar_pagada/

        Body: {
            "fecha_pago": "2025-10-30"  // Opcional
        }
        """
        cuota = self.get_object()

        # Validar que la cuota esté pendiente
        if cuota.estado == 'pagada':
            return Response(
                {'error': 'La cuota ya está marcada como pagada'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar datos
        serializer = MarcarCuotaPagadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Marcar como pagada
        cuota.estado = 'pagada'
        cuota.fecha_pago = serializer.validated_data.get(
            'fecha_pago',
            timezone.now().date()
        )
        cuota.save()

        # Verificar si todas las cuotas están pagadas para actualizar venta
        venta = cuota.venta
        cuotas_pendientes = venta.cuotas.filter(estado__in=['pendiente', 'vencida']).count()

        if cuotas_pendientes == 0:
            venta.estado_pago = 'pagado'
            venta.save()

        response_serializer = self.get_serializer(cuota)

        return Response(
            {
                'message': f'Cuota {cuota.numero_cuota} marcada como pagada',
                'cuota': response_serializer.data
            },
            status=status.HTTP_200_OK
        )
