# apps/ventas/models.py
from django.db import models
from apps.usuarios.models import Usuario
from apps.producto_variante.models import VarianteProducto

TIPO_PAGO_CHOICES = [
    ('contado', 'Contado'),
    ('credito', 'Crédito'),
]

ESTADO_PAGO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('parcial', 'Parcial'),
    ('pagado', 'Pagado'),
]

class Venta(models.Model):
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,  
        related_name='ventas',
        null=True,
        blank=True
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
        cliente_info = self.cliente.email if self.cliente else "Sin cliente"
        return f"Venta #{self.id} - {cliente_info} - {self.get_tipo_pago_display()}"

    def save(self, *args, **kwargs):
        """Validar campos de crédito"""
        if self.tipo_pago == 'credito':
            if not all([self.interes, self.plazo_meses, self.cuota_mensual]):
                raise ValueError("Ventas a crédito requieren interés, plazo y cuota mensual")
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Recalcula el total de la venta basándose en los detalles"""
        from django.db.models import Sum
        
        # Sumar todos los subtotales de los detalles
        subtotal = self.detalles.aggregate(
            total=Sum('subtotal')
        )['total'] or 0
        
        self.total = subtotal
        
        # Si es crédito, calcular total con interés
        if self.tipo_pago == 'credito' and self.interes:
            self.total_con_interes = subtotal * (1 + self.interes / 100)
            
            # Calcular cuota mensual si hay plazo
            if self.plazo_meses:
                self.cuota_mensual = self.total_con_interes / self.plazo_meses
        else:
            self.total_con_interes = None
            self.cuota_mensual = None
        
        self.save()
        return self.total


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
    talla = models.CharField(max_length=5, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        detalles = []
        if self.talla:
            detalles.append(self.talla)
        if self.color:
            detalles.append(self.color)

        detalle_str = f" ({'-'.join(detalles)})" if detalles else ""
        return f"{self.producto_nombre}{detalle_str} x{self.cantidad}"

    def save(self, *args, **kwargs):
        """Auto-calcular subtotal"""
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

