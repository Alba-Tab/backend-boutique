# apps/ventas/models.py
from django.db import models
from decimal import Decimal
from apps.usuarios.models import Usuario
from apps.producto_variante.models import VarianteProducto

class Venta(models.Model):
    TIPO_VENTA = (
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    )

    ORIGEN_CHOICES = (
        ('tienda', 'Tienda Física'),
        ('ecommerce', 'Ecommerce'),
    )

    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_como_cliente',
        limit_choices_to={'rol': 'cliente'}
    )
    vendedor = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas_como_vendedor',
        limit_choices_to={'rol': 'vendedor'}
    )

    correo_cliente = models.EmailField(null=True, blank=True)
    direccion_cliente = models.TextField(null=True, blank=True)
    nombre_cliente = models.CharField(max_length=100, null=True, blank=True)
    telefono_cliente = models.CharField(max_length=20, null=True, blank=True)
    numero_cliente = models.CharField(max_length=50, null=True, blank=True)

    nombre_vendedor = models.CharField(max_length=100, null=True, blank=True)

    estado = models.CharField(max_length=50, default='pendiente')
    fecha = models.DateField(auto_now_add=True)
    tipo_venta = models.CharField(max_length=20, choices=TIPO_VENTA)
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, default='tienda')

    plazo_meses = models.PositiveIntegerField(null=True, blank=True)
    interes = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_con_interes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cuota_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f'Venta #{self.id}'


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    variante_producto = models.ForeignKey(VarianteProducto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    nombre_producto = models.CharField(max_length=100)
    talla = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f'{self.nombre_producto} x {self.cantidad}'

