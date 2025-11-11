from django.contrib import admin
from .models import ModeloEntrenamiento

@admin.register(ModeloEntrenamiento)
class ModeloEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'version', 'fecha_entrenamiento', 'mae', 'r2_score', 'activo']
    list_filter = ['activo', 'fecha_entrenamiento']
    search_fields = ['nombre', 'version']
    readonly_fields = ['fecha_entrenamiento', 'mae', 'r2_score', 'mse', 'registros_entrenamiento']
