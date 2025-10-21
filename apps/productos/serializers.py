from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para mostrar las etiquetas legibles
    genero_display = serializers.CharField(source='get_genero_display', read_only=True)
    temporada_display = serializers.CharField(source='get_temporada_display', read_only=True)
    
    class Meta:
        model = Producto
        fields = '__all__'