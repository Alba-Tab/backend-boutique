from rest_framework import serializers
from .models import ModeloEntrenamiento, AlertaAnomalia


class ModeloEntrenamientoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo de entrenamiento
    """
    class Meta:
        model = ModeloEntrenamiento
        fields = [
            'id', 'nombre', 'version', 'fecha_entrenamiento',
            'mae', 'mse', 'r2_score', 
            'registros_entrenamiento', 'registros_prueba',
            'archivo_modelo', 'activo', 'notas'
        ]
        read_only_fields = [
            'id', 'fecha_entrenamiento', 'mae', 'mse', 'r2_score',
            'registros_entrenamiento', 'registros_prueba', 'archivo_modelo'
        ]


class AlertaAnomaliaSerializer(serializers.ModelSerializer):
    """
    Serializer para alertas de anomalías
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = AlertaAnomalia
        fields = [
            'id', 'tipo', 'tipo_display', 'fecha_deteccion', 'fecha_referencia',
            'descripcion', 'score_anomalia', 
            'producto_id', 'producto_nombre', 
            'valor_real', 'valor_esperado',
            'estado', 'estado_display', 'nota_resolucion'
        ]
        read_only_fields = ['id', 'fecha_deteccion']


class PrediccionGeneralSerializer(serializers.Serializer):
    """
    Serializer para predicciones generales
    """
    periodo = serializers.CharField(help_text='Periodo predicho (ej: 2025-W46)')
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    ventas_predichas = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad_ventas_predichas = serializers.IntegerField()
    confianza = serializers.FloatField(help_text='Nivel de confianza 0-1')
    tendencia = serializers.CharField(help_text='alza/baja/estable')


class PrediccionProductoSerializer(serializers.Serializer):
    """
    Serializer para predicción por producto
    """
    producto_id = serializers.IntegerField()
    producto_nombre = serializers.CharField()
    periodo = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    ventas_predichas = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad_predicha = serializers.IntegerField()
    ventas_historicas = serializers.DecimalField(max_digits=12, decimal_places=2)
    tendencia = serializers.CharField()
    recomendacion = serializers.CharField()


class MetricasModeloSerializer(serializers.Serializer):
    """
    Serializer para métricas del modelo
    """
    mae = serializers.FloatField()
    mse = serializers.FloatField()
    r2_score = serializers.FloatField()
    registros_entrenamiento = serializers.IntegerField()
    registros_prueba = serializers.IntegerField()
    fecha_entrenamiento = serializers.DateTimeField()
    version = serializers.CharField()
