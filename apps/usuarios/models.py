from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
        ('admin', 'Administrador'),
    )

    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True, help_text='Token FCM para notificaciones push')

    def __str__(self):
        return f'{self.username} ({self.rol})'
