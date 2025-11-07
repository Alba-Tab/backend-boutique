from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    class RolChoices(models.TextChoices):
        CLIENTE = 'CLIENTE', 'Cliente'
        ADMINISTRADOR = 'ADMIN', 'Administrador'
        EMPLEADO = 'EMPLEADO', 'Empleado'

    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.CLIENTE
    )
    telefono = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.rol}"
