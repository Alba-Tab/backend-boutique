from rest_framework import serializers
from .models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol', 'telefono', 'fcm_token']
        extra_kwargs = {
            'fcm_token': {'write_only': True}  # No se devuelve en GET por seguridad
        }
