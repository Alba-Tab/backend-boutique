from django.db import models

class Categoria (models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.CharField(max_length=120)