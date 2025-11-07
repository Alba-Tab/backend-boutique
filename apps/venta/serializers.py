# apps/venta/serializers.py
from rest_framework import serializers
from .models import DetalleVenta, Venta


class DetalleVentaSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR y CREAR/ACTUALIZAR detalles de venta
    """
    # Campos calculados (solo lectura)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    producto_nombre = serializers.CharField(read_only=True)
    talla = serializers.CharField(read_only=True)
    color = serializers.CharField(read_only=True)
    
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
        read_only_fields = ['id', 'subtotal', 'producto_nombre', 'talla', 'color']
    
    def create(self, validated_data):
        """Crear detalle con snapshot de datos de la variante"""
        variante = validated_data['variante']
        
        # Snapshot: guardar datos actuales del producto
        validated_data['producto_nombre'] = variante.producto.nombre
        validated_data['talla'] = variante.talla
        validated_data['color'] = variante.color
        
        # Si no se envía precio, usar el de la variante
        if 'precio_unitario' not in validated_data:
            validated_data['precio_unitario'] = variante.precio_venta
        
        return super().create(validated_data)
    
    def validate_cantidad(self, value):
        """Validar cantidad positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value
    
    def validate(self, data):
        """Validar stock disponible"""
        if self.instance is None:  # Solo al crear
            variante = data.get('variante')
            cantidad = data.get('cantidad')
            
            if variante and cantidad and variante.stock < cantidad:
                raise serializers.ValidationError({
                    'cantidad': f'Stock insuficiente. Disponible: {variante.stock}'
                })
        
        return data

class VentaListSerializer(serializers.ModelSerializer):
    """Sin detalles"""
    cliente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = ['id', 'cliente', 'cliente_nombre', 'fecha', 'total', 'tipo_pago', 'estado_pago']

    def get_cliente_nombre(self, obj):
        return obj.cliente.username if obj.cliente else 'Cliente anónimo'


class VentaDetailSerializer(serializers.ModelSerializer):
    """Con detalles anidados"""
    cliente_nombre = serializers.SerializerMethodField()
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    monto_total_pagar = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = [
            'id', 'cliente', 'cliente_nombre', 'fecha', 'total',
            'tipo_pago', 'estado_pago', 'interes', 'total_con_interes',
            'plazo_meses', 'cuota_mensual', 'monto_total_pagar',
            'detalles'
        ]

    def get_cliente_nombre(self, obj):
        return obj.cliente.email if obj.cliente else 'Cliente anónimo'
    
    def get_monto_total_pagar(self, obj):
        """
        Retorna el monto TOTAL que el cliente debe pagar:
        - Contado: total (sin interés)
        - Crédito: total_con_interes (con interés)
        """
        if obj.tipo_pago == 'credito' and obj.total_con_interes:
            return str(obj.total_con_interes)
        return str(obj.total)


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


