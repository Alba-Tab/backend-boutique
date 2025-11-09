from rest_framework import serializers
from .models import VarianteProducto

class VarianteProductoSerializer(serializers.ModelSerializer):
    hay_stock = serializers.BooleanField(read_only=True)
    stock_bajo = serializers.BooleanField(read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    
    class Meta:
        model = VarianteProducto
        fields = [
            'id', 'producto', 'producto_nombre', 'talla',
            'precio', 'stock', 'stock_minimo', 'hay_stock', 'stock_bajo'
        ]

    def validate(self, data):
        """Validaciones adicionales"""
        if data.get('precio', 0) < 0:
            raise serializers.ValidationError({
                'precio': 'El precio no puede ser negativo'
            })

        if data.get('stock', 0) < 0:
            raise serializers.ValidationError({
                'stock': 'El stock no puede ser negativo'
            })

        return data
