from rest_framework import serializers
from .models import VarianteProducto

class VarianteProductoSerializer(serializers.ModelSerializer):
    hay_stock = serializers.BooleanField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = VarianteProducto
        fields = [
            'id', 'producto', 'producto_nombre', 'talla', 'color',
            'precio_venta', 'precio_costo', 'imagen', 'stock',
            'stock_minimo', 'hay_stock', 'stock_bajo'
        ]

    def validate(self, data):
        """Validaciones adicionales"""
        if data.get('precio_venta', 0) < data.get('precio_costo', 0):
            raise serializers.ValidationError({
                'precio_venta': 'El precio de venta no puede ser menor al precio de costo'
            })

        if data.get('stock', 0) < 0:
            raise serializers.ValidationError({
                'stock': 'El stock no puede ser negativo'
            })

        return data
