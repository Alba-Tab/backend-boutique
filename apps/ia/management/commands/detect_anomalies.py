"""
Management command para detectar anomalías
Uso: python manage.py detect_anomalies [--dias N]
"""
from django.core.management.base import BaseCommand
from apps.ia.services import AnomalyDetector


class Command(BaseCommand):
    help = 'Detecta anomalías en las ventas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Número de días a analizar (default: 30)'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        
        self.stdout.write(self.style.WARNING(f'🔍 Analizando ventas de los últimos {dias} días...'))
        self.stdout.write('')
        
        try:
            detector = AnomalyDetector()
            alertas = detector.detectar_anomalias(dias_analisis=dias)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Análisis completado'))
            self.stdout.write('')
            self.stdout.write(f"📊 Resumen:")
            self.stdout.write(f"   Anomalías detectadas: {len(alertas)}")
            self.stdout.write('')
            
            if alertas:
                self.stdout.write("🚨 Alertas generadas:")
                for alerta in alertas:
                    self.stdout.write(f"   • {alerta.get_tipo_display()} - {alerta.fecha_referencia}")
                    self.stdout.write(f"     {alerta.descripcion}")
                    self.stdout.write('')
            else:
                self.stdout.write("✅ No se detectaron anomalías en el período analizado")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
