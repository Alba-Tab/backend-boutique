from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    
    def __str__(self) -> str:
        return super().__str__()
