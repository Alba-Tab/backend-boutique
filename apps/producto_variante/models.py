from django.db import models
from django.core.exceptions import ValidationError
from apps.productos.models import Producto

class VarianteProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    talla = models.CharField(
        max_length=5,
        choices=[
            ('XS', 'Extra Small'),
            ('S', 'Small'),
            ('M', 'Medium'),
            ('L', 'Large'),
            ('XL', 'Extra Large'),
            ('XXL', 'Double Extra Large'),
        ],
        blank=True,
        null=True
    )
    color = models.CharField(max_length=30, blank=True, null=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    imagen = models.URLField(max_length=200, blank=True, null=True)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Variante de Producto'
        verbose_name_plural = 'Variantes de Productos'
        # Evita duplicados de talla+color para el mismo producto
        unique_together = [['producto', 'talla', 'color']]

    def __str__(self):
        partes = [self.producto.nombre]
        if self.talla:
            partes.append(self.talla)
        if self.color:
            partes.append(self.color)
        return " - ".join(partes)

    def hay_stock(self):
        """Verifica si hay stock disponible"""
        return self.stock > 0

    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        if self.precio_venta < self.precio_costo:
            raise ValidationError('El precio de venta no puede ser menor al precio de costo')
        if self.stock < 0:
            raise ValidationError('El stock no puede ser negativo')
        if self.stock_minimo < 0:
            raise ValidationError('El stock mínimo no puede ser negativo')
