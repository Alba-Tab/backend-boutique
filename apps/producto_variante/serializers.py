from rest_framework import serializers
from .models import VarianteProducto

class VarianteProductoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='producto.nombre', read_only=True)
    
    class Meta:
        model = VarianteProducto
        fields = ['id', 'nombre', 'producto', 'talla', 'color', 'precio_venta', 'precio_costo', 'stock', 'stock_minimo']
