from django.db import models
from django.core.exceptions import ValidationError
from apps.productos.models import Producto

class VarianteProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    talla = models.CharField(max_length=10, null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    stock_minimo = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.producto.nombre} - Talla {self.talla or "Sin talla"}'

    def hay_stock(self):
        """Verifica si hay stock disponible"""
        return self.stock > 0

    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        if self.stock < 0:
            raise ValidationError('El stock no puede ser negativo')
        if self.stock_minimo < 0:
            raise ValidationError('El stock mínimo no puede ser negativo')
        if self.precio < 0:
            raise ValidationError('El precio no puede ser negativo')
