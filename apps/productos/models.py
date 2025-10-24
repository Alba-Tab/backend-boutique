from django.db import models
from apps.categorias.models import Categoria
class Producto (models.Model):
    nombre = models.CharField(max_length=60)
    descripcion =  models.CharField(max_length=120)
    precio = models.IntegerField()
    stock = models.IntegerField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE,related_name='categorias', null=True,blank=True)
    
