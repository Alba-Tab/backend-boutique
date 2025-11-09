# apps/venta/serializers.py
from rest_framework import serializers
from .models import DetalleVenta, Venta


class DetalleVentaSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR y CREAR/ACTUALIZAR detalles de venta
    """
    # Campos calculados (solo lectura)
    sub_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    nombre_producto = serializers.CharField(read_only=True)
    talla = serializers.CharField(read_only=True)
    
    class Meta:
        model = DetalleVenta
        fields = [
            'id',
            'variante_producto',
            'cantidad',
            'precio_unitario',
            'sub_total',
            'nombre_producto',
            'talla'
        ]
        read_only_fields = ['id', 'sub_total', 'nombre_producto', 'talla']
    
    def create(self, validated_data):
        """Crear detalle con snapshot de datos de la variante"""
        variante = validated_data['variante_producto']
        
        # Snapshot: guardar datos actuales del producto
        validated_data['nombre_producto'] = variante.producto.nombre
        validated_data['talla'] = variante.talla
        
        # Calcular sub_total
        validated_data['sub_total'] = validated_data['cantidad'] * validated_data['precio_unitario']
        
        # Si no se envía precio, usar el de la variante
        if 'precio_unitario' not in validated_data:
            validated_data['precio_unitario'] = variante.precio
        
        return super().create(validated_data)
    
    def validate_cantidad(self, value):
        """Validar cantidad positiva"""
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0")
        return value
    
    def validate(self, data):
        """Validar stock disponible"""
        if self.instance is None:  # Solo al crear
            variante = data.get('variante_producto')
            cantidad = data.get('cantidad')
            
            if variante and cantidad and variante.stock < cantidad:
                raise serializers.ValidationError({
                    'cantidad': f'Stock insuficiente. Disponible: {variante.stock}'
                })
        
        return data

class VentaListSerializer(serializers.ModelSerializer):
    """Sin detalles"""
    cliente_nombre = serializers.SerializerMethodField()
    vendedor_nombre = serializers.CharField(source='nombre_vendedor', read_only=True)

    class Meta:
        model = Venta
        fields = [
            'id', 'cliente', 'cliente_nombre', 'vendedor', 'vendedor_nombre',
            'fecha', 'total', 'tipo_venta', 'estado'
        ]

    def get_cliente_nombre(self, obj):
        if obj.nombre_cliente:
            return obj.nombre_cliente
        return obj.cliente.username if obj.cliente else 'Cliente anónimo'


class VentaDetailSerializer(serializers.ModelSerializer):
    """Con detalles anidados"""
    cliente_nombre = serializers.SerializerMethodField()
    vendedor_nombre = serializers.CharField(source='nombre_vendedor', read_only=True)
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    monto_total_pagar = serializers.SerializerMethodField()

    class Meta:
        model = Venta
        fields = [
            'id', 'cliente', 'cliente_nombre', 'vendedor', 'vendedor_nombre',
            'correo_cliente', 'direccion_cliente', 'nombre_cliente',
            'telefono_cliente', 'numero_cliente',
            'fecha', 'total', 'tipo_venta', 'estado',
            'interes', 'total_con_interes', 'plazo_meses', 'cuota_mensual',
            'monto_total_pagar', 'detalles'
        ]

    def get_cliente_nombre(self, obj):
        if obj.nombre_cliente:
            return obj.nombre_cliente
        return obj.cliente.email if obj.cliente else 'Cliente anónimo'
    
    def get_monto_total_pagar(self, obj):
        """
        Retorna el monto TOTAL que el cliente debe pagar:
        - Contado: total (sin interés)
        - Crédito: total_con_interes (con interés)
        """
        if obj.tipo_venta == 'credito' and obj.total_con_interes:
            return str(obj.total_con_interes)
        return str(obj.total)


class CrearVentaSerializer(serializers.Serializer):
    """Para crear venta"""
    cliente = serializers.IntegerField(required=False, allow_null=True)
    vendedor = serializers.IntegerField(required=True)
    
    # Datos opcionales del cliente
    correo_cliente = serializers.EmailField(required=False, allow_null=True)
    direccion_cliente = serializers.CharField(required=False, allow_null=True)
    nombre_cliente = serializers.CharField(max_length=100, required=False, allow_null=True)
    telefono_cliente = serializers.CharField(max_length=20, required=False, allow_null=True)
    numero_cliente = serializers.CharField(max_length=50, required=False, allow_null=True)
    
    tipo_venta = serializers.ChoiceField(choices=['contado', 'credito'])
    items = serializers.ListField(child=serializers.DictField())
    interes = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    plazo_meses = serializers.IntegerField(required=False)
    estado = serializers.CharField(max_length=50, required=False, default='pendiente')

    def validate(self, data):
        if data['tipo_venta'] == 'credito':
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


