


from django.db import models

from apps.venta.models import Venta


class CuotaCredito(models.Model):
    """
    Cuotas mensuales para ventas a crédito
    """
    ESTADO_CUOTA_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    ]

    # Relaciones
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='cuotas'
    )

    # Información de la cuota
    numero_cuota = models.IntegerField(help_text="Número de cuota (1, 2, 3...)")
    fecha_vencimiento = models.DateField()
    monto_cuota = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CUOTA_CHOICES,
        default='pendiente'
    )
    fecha_pago = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Cuota de Crédito'
        verbose_name_plural = 'Cuotas de Crédito'
        ordering = ['venta', 'numero_cuota']
        unique_together = ['venta', 'numero_cuota']  # No duplicar cuotas

    def __str__(self):
        return f"Cuota {self.numero_cuota}/{self.venta.plazo_meses} - Venta #{self.venta.id}"

    @property
    def esta_vencida(self):
        """Verifica si la cuota está vencida"""
        from django.utils import timezone
        if self.estado != 'pagada':
            return timezone.now().date() > self.fecha_vencimiento
        return False
