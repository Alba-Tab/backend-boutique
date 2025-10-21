from django.db import models
from apps.categorias.models import Categoria
class Producto (models.Model):
    #('valor_guardado_en_BD', 'etiqueta_mostrada_en_UI')
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('U', 'Unisex')
    ]
    TEMPORADA_CHOISES = [
        # (Valor en BD, Etiqueta para el usuario)
        ('INV', 'Invierno'),
        ('OTÑ', 'Otoño'),
        ('PRI', 'Primavera'),
        ('VER', 'Verano'),
        ('ALL','all')
    ]
    nombre = models.CharField(max_length=60)
    descripcion =  models.CharField(max_length=120)
    temporada = models.CharField(max_length=60, choices=TEMPORADA_CHOISES)
    genero = models.CharField(max_length=1,choices=GENERO_CHOICES)
    marca = models.CharField(max_length=60)
    
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE,related_name='categorias', null=True,blank=True)
    
