from django.db import models

class Categoria (models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.CharField(max_length=120)
    
    def __str__(self):
        return f"Categoria #{self.id} - {self.nombre}"