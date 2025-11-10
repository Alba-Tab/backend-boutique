from rest_framework import serializers

class ReportEmailSerializer(serializers.Serializer):
    """Serializer para solicitar reporte por correo"""
    user_email = serializers.EmailField(default='garcia.brayan3001@gmail.com')