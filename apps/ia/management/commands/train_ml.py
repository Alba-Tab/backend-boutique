"""
Management command para entrenar modelos de ML
Uso: python manage.py train_ml
"""
from django.core.management.base import BaseCommand
from apps.ia.services import MLService


class Command(BaseCommand):
    help = 'Entrena o re-entrena los modelos de Machine Learning'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🤖 Iniciando entrenamiento de modelos ML...'))
        self.stdout.write('')
        
        try:
            ml_service = MLService()
            resultado = ml_service.entrenar()
            
            if resultado['success']:
                self.stdout.write(self.style.SUCCESS('✅ Entrenamiento completado exitosamente'))
                self.stdout.write('')
                self.stdout.write(f"📊 Métricas:")
                self.stdout.write(f"   MAE: {resultado['metricas']['mae']:.2f}")
                self.stdout.write(f"   R² Score: {resultado['metricas']['r2']:.4f}")
                self.stdout.write(f"   Registros entrenamiento: {resultado['metricas']['registros_train']}")
                self.stdout.write('')
                self.stdout.write(f"💾 Modelo guardado: {resultado['archivo']}")
                self.stdout.write(f"📌 Versión: {resultado['version']}")
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {resultado["error"]}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error inesperado: {str(e)}'))
