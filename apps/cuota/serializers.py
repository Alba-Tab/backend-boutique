from rest_framework import serializers
from .models import CuotaCredito


class CuotaSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar cuotas
    """
    venta_id = serializers.IntegerField(source='venta.id', read_only=True)
    cliente_nombre = serializers.CharField(source='venta.cliente.email', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)

    class Meta:
        model = CuotaCredito
        fields = [
            'id',
            'venta',
            'venta_id',
            'cliente_nombre',
            'numero_cuota',
            'fecha_vencimiento',
            'monto_cuota',
            'estado',
            'estado_display',
            'fecha_pago',
            'esta_vencida'
        ]
        read_only_fields = ['esta_vencida']


class MarcarCuotaPagadaSerializer(serializers.Serializer):
    """
    Serializer para marcar una cuota como pagada
    """
    fecha_pago = serializers.DateField(
        required=False,
        help_text="Fecha del pago (opcional, por defecto hoy)"
    )
