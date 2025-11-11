from django.db import models
from django.utils import timezone


class ModeloEntrenamiento(models.Model):
    """
    Modelo para rastrear los entrenamientos de ML realizados
    """
    nombre = models.CharField(max_length=100, default='modelo_ventas')
    version = models.CharField(max_length=50)
    fecha_entrenamiento = models.DateTimeField(default=timezone.now)
    
    # Métricas del modelo
    mae = models.FloatField(help_text='Mean Absolute Error', null=True, blank=True)
    mse = models.FloatField(help_text='Mean Squared Error', null=True, blank=True)
    r2_score = models.FloatField(help_text='R² Score', null=True, blank=True)
    
    # Metadatos del entrenamiento
    registros_entrenamiento = models.IntegerField(default=0)
    registros_prueba = models.IntegerField(default=0)
    archivo_modelo = models.CharField(max_length=255, help_text='Ruta del archivo .pkl')
    
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_entrenamiento']
        verbose_name = 'Modelo de Entrenamiento'
        verbose_name_plural = 'Modelos de Entrenamiento'
    
    def __str__(self):
        return f"{self.nombre} v{self.version} - {self.fecha_entrenamiento.strftime('%Y-%m-%d %H:%M')}"


class AlertaAnomalia(models.Model):
    """
    Modelo para almacenar alertas de anomalías detectadas
    """
    TIPO_CHOICES = (
        ('venta_baja', 'Venta inusualmente baja'),
        ('venta_alta', 'Venta inusualmente alta'),
        ('producto_anomalo', 'Producto con comportamiento anómalo'),
        ('tendencia_negativa', 'Tendencia negativa detectada'),
    )
    
    ESTADO_CHOICES = (
        ('nueva', 'Nueva'),
        ('revisada', 'Revisada'),
        ('resuelta', 'Resuelta'),
        ('ignorada', 'Ignorada'),
    )
    
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    fecha_deteccion = models.DateTimeField(default=timezone.now)
    fecha_referencia = models.DateField(help_text='Fecha de la venta anómala')
    
    descripcion = models.TextField()
    score_anomalia = models.FloatField(help_text='Score de anomalía (-1 = anomalía, 1 = normal)')
    
    # Datos contextuales
    producto_id = models.IntegerField(null=True, blank=True)
    producto_nombre = models.CharField(max_length=200, null=True, blank=True)
    valor_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_esperado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='nueva')
    nota_resolucion = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_deteccion']
        verbose_name = 'Alerta de Anomalía'
        verbose_name_plural = 'Alertas de Anomalías'
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_referencia}"
