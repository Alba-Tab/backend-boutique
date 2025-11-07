

from django.db import models

from apps.venta.models import Venta


class Pago(models.Model):

    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('qr', 'QR'),
    ]

    # Relaciones
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    
    # Relación opcional con cuota (para pagos a crédito)
    cuota = models.ForeignKey(
        'cuota.CuotaCredito',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos',
        help_text="Cuota específica que se está pagando (opcional)"
    )

    # Información del pago
    fecha_pago = models.DateTimeField(auto_now_add=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES)
    referencia_pago = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de transacción, voucher, etc."
    )

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']

    def __str__(self):
        cuota_info = f" - Cuota {self.cuota.numero_cuota}" if self.cuota else ""
        return f"Pago #{self.id} - Venta #{self.venta.id}{cuota_info} - Bs.{self.monto_pagado}"
