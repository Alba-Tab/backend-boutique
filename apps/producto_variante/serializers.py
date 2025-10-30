from rest_framework import serializers
from .models import VarianteProducto

class VarianteProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VarianteProducto
        fields = '__all__'
