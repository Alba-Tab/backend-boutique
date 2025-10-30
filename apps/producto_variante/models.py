from django.db import models

from apps.productos.models import Producto
class VarianteProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    talla = models.CharField(max_length=5, choices=[
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    ])
    color = models.CharField(max_length=30)
    precio_venta = models.IntegerField(default=0)
    precio_costo = models.IntegerField(default=0)
    imagen = models.URLField(max_length=200, blank=True , null=True)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla} - {self.color}"
