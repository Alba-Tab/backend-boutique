# apps/detalle_venta/serializers.py
from rest_framework import serializers
from .models import DetalleVenta, Venta

class DetalleVentaSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar detalles de venta
    Se usa DESDE VentaSerializer
    """
    class Meta:
        model = DetalleVenta
        fields = [
            'id',
            'variante',
            'cantidad',
            'precio_unitario',
            'subtotal',
            'producto_nombre',
            'talla',
            'color'
        ]

class VentaListSerializer(serializers.ModelSerializer):
    """Sin detalles"""
    cliente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = ['id', 'cliente', 'cliente_nombre', 'fecha', 'total', 'tipo_pago', 'estado_pago']

    def get_cliente_nombre(self, obj):
        """Retorna email del cliente o 'Cliente anónimo'"""
        return obj.cliente.email if obj.cliente else 'Cliente anónimo'


class VentaDetailSerializer(serializers.ModelSerializer):
    """Con detalles anidados"""
    cliente_nombre = serializers.SerializerMethodField()
    detalles = DetalleVentaSerializer(many=True, read_only=True)

    class Meta:
        model = Venta
        fields = [
            'id', 'cliente', 'cliente_nombre', 'fecha', 'total',
            'tipo_pago', 'estado_pago', 'interes', 'total_con_interes',
            'plazo_meses', 'cuota_mensual',
            'detalles'
        ]

    def get_cliente_nombre(self, obj):
        """Retorna email del cliente o 'Cliente anónimo'"""
        return obj.cliente.email if obj.cliente else 'Cliente anónimo'


class CrearVentaSerializer(serializers.Serializer):
    """Para crear venta"""
    cliente = serializers.IntegerField(required=False, allow_null=True)  # ⬅️ OPCIONAL
    tipo_pago = serializers.ChoiceField(choices=['contado', 'credito'])
    items = serializers.ListField(child=serializers.DictField())
    interes = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    plazo_meses = serializers.IntegerField(required=False)

    def validate(self, data):
        if data['tipo_pago'] == 'credito':
            if not data.get('interes') or not data.get('plazo_meses'):
                raise serializers.ValidationError(
                    "Ventas a crédito requieren 'interes' y 'plazo_meses'"
                )
        if not data.get('items'):
            raise serializers.ValidationError("Debe incluir al menos un item")

        for item in data['items']:
            if 'variante_id' not in item or 'cantidad' not in item:
                raise serializers.ValidationError(
                    "Cada item debe tener 'variante_id' y 'cantidad'"
                )
        return data


