from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'genero', 'descripcion', 'marca', 'imagen_url', 'stock']

    def get_imagen_url(self, obj):
        return obj.image.url if obj.image else None
    
    def get_stock(self, obj):
        total_stock = sum(variante.stock for variante in obj.variantes.all())
        return total_stock