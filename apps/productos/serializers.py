from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField(read_only=True)
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'genero', 'descripcion', 'marca', 'image', 'stock']
    
    def get_stock(self, obj):
        """Calcula el stock total sumando todas las variantes"""
        total_stock = sum(variante.stock for variante in obj.variantes.all())
        return total_stock