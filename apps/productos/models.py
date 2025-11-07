from django.db import models
from apps.categorias.models import Categoria
class Producto (models.Model):
    nombre = models.CharField(max_length=60)
    descripcion =  models.CharField(max_length=120)
    precio_base = models.IntegerField(default=0)
    marca = models.CharField(max_length=30, null=True, blank=True)
    genero = models.CharField(max_length=10, choices=[
        ('Hombre', 'Hombre'),
        ('Mujer', 'Mujer'),
        ('Unisex', 'Unisex'),
    ], null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE,related_name='productos', null=True,blank=True)

    def __str__(self):
        return self.nombre
