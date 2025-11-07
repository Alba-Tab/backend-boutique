from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = ['id','nombre','categoria','precio_base', 'genero', 'descripcion', 'imagen_url', 'stock', 'categoria_nombre']

    def get_imagen_url(self, obj):
        return obj.imagen.url if obj.imagen else None
    
    def get_stock(self, obj):
        total_stock = sum(variante.stock for variante in obj.variantes.all())
        return total_stock