from rest_framework import serializers
from .models import Pago


class PagoSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar pagos
    """
    venta_id = serializers.IntegerField(source='venta.id', read_only=True)
    cuota_numero = serializers.IntegerField(source='cuota.numero_cuota', read_only=True, allow_null=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)

    class Meta:
        model = Pago
        fields = [
            'id',
            'venta',
            'venta_id',
            'cuota',
            'cuota_numero',
            'fecha_pago',
            'monto_pagado',
            'metodo_pago',
            'metodo_pago_display',
            'referencia_pago'
        ]
        read_only_fields = ['fecha_pago']


class RegistrarPagoSerializer(serializers.Serializer):
    """
    Serializer para registrar un nuevo pago
    """
    venta = serializers.IntegerField(help_text="ID de la venta")
    cuota = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID de cuota específica a pagar (opcional)"
    )
    monto_pagado = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto del pago"
    )
    metodo_pago = serializers.ChoiceField(
        choices=['efectivo', 'tarjeta', 'qr'],
        help_text="Método de pago"
    )
    referencia_pago = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Referencia opcional del pago"
    )

    def validate_monto_pagado(self, value):
        """Validar que el monto sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value


class PagoAlContadoSerializer(serializers.Serializer):
    """
    Serializer para registrar pago al contado (POS)
    """
    metodo_pago = serializers.ChoiceField(
        choices=['efectivo', 'tarjeta', 'qr'],
        help_text="Método de pago"
    )
    referencia_pago = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Referencia opcional del pago"
    )
