# apps/ventas/models.py
from django.db import models
from apps.usuarios.models import Usuario
from apps.producto_variante.models import VarianteProducto


class Venta(models.Model):

    TIPO_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]

    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('parcial', 'Parcial'),
        ('pagado', 'Pagado'),
    ]

    # Relaciones
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,  # No borrar si tiene ventas
        related_name='ventas',
        null=True,      # ⬅️ Puede ser NULL (sin cliente)
        blank=True      # ⬅️ Puede estar vacío
    )

    # Información básica
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total sin interés"
    )
    tipo_pago = models.CharField(
        max_length=10,
        choices=TIPO_PAGO_CHOICES,
        default='contado'
    )
    estado_pago = models.CharField(
        max_length=10,
        choices=ESTADO_PAGO_CHOICES,
        default='pendiente'
    )

    # SOLO SI ES CRÉDITO (pueden ser null)
    interes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Porcentaje de interés (ej: 15.00 = 15%)"
    )
    total_con_interes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total con interés aplicado"
    )
    plazo_meses = models.IntegerField(
        null=True,
        blank=True,
        help_text="Número de meses para pagar"
    )
    cuota_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Monto de cada cuota mensual"
    )

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha']),
            models.Index(fields=['cliente', 'estado_pago']),
        ]

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente.email} - {self.get_tipo_pago_display()}"

    def save(self, *args, **kwargs):
        """Validar campos de crédito"""
        if self.tipo_pago == 'credito':
            if not all([self.interes, self.plazo_meses, self.cuota_mensual]):
                raise ValueError("Ventas a crédito requieren interés, plazo y cuota mensual")
        super().save(*args, **kwargs)


class DetalleVenta(models.Model):

    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,  # Si borras venta, borras detalles
        related_name='detalles'
    )
    variante = models.ForeignKey(
        VarianteProducto,
        on_delete=models.PROTECT,  # No borrar variantes con ventas
        related_name='detalles_venta'
    )

    # Datos del item
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio al momento de la venta"
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="cantidad * precio_unitario"
    )

    # Snapshot de datos (por si cambian después)
    producto_nombre = models.CharField(max_length=60)
    talla = models.CharField(max_length=5)
    color = models.CharField(max_length=30)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        return f"{self.producto_nombre} ({self.talla}-{self.color}) x{self.cantidad}"

    def save(self, *args, **kwargs):
        """Auto-calcular subtotal"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

