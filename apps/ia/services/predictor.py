import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Avg, Count
from django.utils import timezone

from apps.venta.models import Venta, DetalleVenta
from apps.productos.models import Producto
from .ml_service import MLService


class Predictor:
    
    def __init__(self):
        self.ml_service = MLService()
        self.ml_service.cargar_modelos()
    
    def predecir_ventas_generales(self, periodo='semanal', cantidad_periodos=4):
        if not self.ml_service.modelo_ventas:
            raise ValueError("No hay modelo entrenado disponible")
        
        predicciones = []
        fecha_actual = timezone.now().date()
        
        # Obtener estadísticas históricas para contexto
        ventas_historicas = Venta.objects.filter(
            fecha__gte=fecha_actual - timedelta(days=90)
        )
        
        promedio_diario = ventas_historicas.aggregate(
            promedio=Avg('total')
        )['promedio'] or 0
        
        for i in range(cantidad_periodos):
            if periodo == 'semanal':
                # Calcular inicio y fin de semana
                dias_adelante = 7 * (i + 1)
                fecha_inicio = fecha_actual + timedelta(days=7*i)
                fecha_fin = fecha_inicio + timedelta(days=6)
                periodo_str = f"{fecha_inicio.year}-W{fecha_inicio.isocalendar()[1]}"
                
            else:  # mensual
                # Calcular mes siguiente
                mes_futuro = fecha_actual.month + i + 1
                anio_futuro = fecha_actual.year + (mes_futuro - 1) // 12
                mes_futuro = ((mes_futuro - 1) % 12) + 1
                
                fecha_inicio = datetime(anio_futuro, mes_futuro, 1).date()
                # Último día del mes
                if mes_futuro == 12:
                    fecha_fin = datetime(anio_futuro, 12, 31).date()
                else:
                    fecha_fin = (datetime(anio_futuro, mes_futuro + 1, 1) - timedelta(days=1)).date()
                
                periodo_str = f"{anio_futuro}-{mes_futuro:02d}"
            
            # Simular features para el período futuro
            # Usamos promedios históricos como base
            dias_periodo = (fecha_fin - fecha_inicio).days + 1
            
            # Predicción simple: promedio histórico * días del período
            ventas_predichas = float(promedio_diario) * dias_periodo if promedio_diario else 0
            
            # Ajustar por tendencia histórica
            tendencia = self._calcular_tendencia()
            ventas_predichas *= (1 + tendencia)
            
            # Estimar cantidad de ventas (asumiendo ticket promedio)
            ticket_promedio = ventas_historicas.aggregate(Avg('total'))['total__avg'] or 100
            cantidad_ventas = int(ventas_predichas / float(ticket_promedio))
            
            # Nivel de confianza basado en cantidad de datos históricos
            confianza = min(0.95, ventas_historicas.count() / 100)
            
            predicciones.append({
                'periodo': periodo_str,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'ventas_predichas': Decimal(str(round(ventas_predichas, 2))),
                'cantidad_ventas_predichas': cantidad_ventas,
                'confianza': round(confianza, 2),
                'tendencia': 'alza' if tendencia > 0.05 else 'baja' if tendencia < -0.05 else 'estable'
            })
        
        return predicciones
    
    def predecir_ventas_producto(self, producto_id, periodo='mensual', cantidad_periodos=3):
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            raise ValueError(f"Producto con ID {producto_id} no encontrado")
        
        # Obtener historial de ventas del producto
        fecha_limite = timezone.now().date() - timedelta(days=180)
        
        detalles = DetalleVenta.objects.filter(
            variante_producto__producto_id=producto_id,
            venta__fecha__gte=fecha_limite
        ).select_related('venta')
        
        if not detalles.exists():
            # Si no hay historial, retornar predicción conservadora
            return self._prediccion_sin_historial(producto, periodo, cantidad_periodos)
        
        # Calcular estadísticas históricas
        total_vendido = detalles.aggregate(
            total=Sum('sub_total'),
            cantidad=Sum('cantidad')
        )
        
        ventas_por_mes = detalles.values(
            'venta__fecha__year', 'venta__fecha__month'
        ).annotate(
            total=Sum('sub_total'),
            cantidad=Sum('cantidad')
        )
        
        promedio_mensual = total_vendido['total'] / max(1, len(set(
            (d['venta__fecha__year'], d['venta__fecha__month']) for d in ventas_por_mes
        )))
        
        predicciones = []
        fecha_actual = timezone.now().date()
        
        for i in range(cantidad_periodos):
            if periodo == 'semanal':
                fecha_inicio = fecha_actual + timedelta(days=7*i)
                fecha_fin = fecha_inicio + timedelta(days=6)
                periodo_str = f"{fecha_inicio.year}-W{fecha_inicio.isocalendar()[1]}"
                factor_periodo = 0.25  # 1 semana = ~0.25 meses
            else:
                mes_futuro = fecha_actual.month + i + 1
                anio_futuro = fecha_actual.year + (mes_futuro - 1) // 12
                mes_futuro = ((mes_futuro - 1) % 12) + 1
                
                fecha_inicio = datetime(anio_futuro, mes_futuro, 1).date()
                if mes_futuro == 12:
                    fecha_fin = datetime(anio_futuro, 12, 31).date()
                else:
                    fecha_fin = (datetime(anio_futuro, mes_futuro + 1, 1) - timedelta(days=1)).date()
                
                periodo_str = f"{anio_futuro}-{mes_futuro:02d}"
                factor_periodo = 1.0
            
            # Predicción basada en promedio histórico
            ventas_predichas = float(promedio_mensual) * factor_periodo
            
            # Calcular tendencia específica del producto
            tendencia_producto = self._calcular_tendencia_producto(producto_id)
            ventas_predichas *= (1 + tendencia_producto)
            
            # Cantidad predicha (unidades)
            precio_promedio = detalles.aggregate(Avg('precio_unitario'))['precio_unitario__avg'] or 100
            cantidad_predicha = int(ventas_predichas / float(precio_promedio))
            
            # Determinar recomendación
            if tendencia_producto > 0.1:
                recomendacion = "Alta demanda esperada - Aumentar stock"
            elif tendencia_producto < -0.1:
                recomendacion = "Baja demanda esperada - Considerar promoción"
            else:
                recomendacion = "Demanda estable - Mantener stock actual"
            
            predicciones.append({
                'producto_id': producto_id,
                'producto_nombre': producto.nombre,
                'periodo': periodo_str,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'ventas_predichas': Decimal(str(round(ventas_predichas, 2))),
                'cantidad_predicha': cantidad_predicha,
                'ventas_historicas': Decimal(str(round(float(promedio_mensual), 2))),
                'tendencia': 'alza' if tendencia_producto > 0.05 else 'baja' if tendencia_producto < -0.05 else 'estable',
                'recomendacion': recomendacion
            })
        
        return predicciones
    
    def _prediccion_sin_historial(self, producto, periodo, cantidad_periodos):

        predicciones = []
        fecha_actual = timezone.now().date()
        
        for i in range(cantidad_periodos):
            if periodo == 'semanal':
                fecha_inicio = fecha_actual + timedelta(days=7*i)
                fecha_fin = fecha_inicio + timedelta(days=6)
                periodo_str = f"{fecha_inicio.year}-W{fecha_inicio.isocalendar()[1]}"
            else:
                mes_futuro = fecha_actual.month + i + 1
                anio_futuro = fecha_actual.year + (mes_futuro - 1) // 12
                mes_futuro = ((mes_futuro - 1) % 12) + 1
                
                fecha_inicio = datetime(anio_futuro, mes_futuro, 1).date()
                if mes_futuro == 12:
                    fecha_fin = datetime(anio_futuro, 12, 31).date()
                else:
                    fecha_fin = (datetime(anio_futuro, mes_futuro + 1, 1) - timedelta(days=1)).date()
                
                periodo_str = f"{anio_futuro}-{mes_futuro:02d}"
            
            predicciones.append({
                'producto_id': producto.id,
                'producto_nombre': producto.nombre,
                'periodo': periodo_str,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'ventas_predichas': Decimal('0.00'),
                'cantidad_predicha': 0,
                'ventas_historicas': Decimal('0.00'),
                'tendencia': 'sin_datos',
                'recomendacion': 'Producto nuevo - Sin datos históricos suficientes'
            })
        
        return predicciones
    
    def _calcular_tendencia(self):

        fecha_actual = timezone.now().date()
        
        # Últimos 3 meses
        ventas_recientes = Venta.objects.filter(
            fecha__gte=fecha_actual - timedelta(days=90),
            fecha__lt=fecha_actual
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # 3 meses anteriores
        ventas_anteriores = Venta.objects.filter(
            fecha__gte=fecha_actual - timedelta(days=180),
            fecha__lt=fecha_actual - timedelta(days=90)
        ).aggregate(total=Sum('total'))['total'] or 0
        
        if ventas_anteriores > 0:
            return (float(ventas_recientes) - float(ventas_anteriores)) / float(ventas_anteriores)
        
        return 0.0
    
    def _calcular_tendencia_producto(self, producto_id):

        fecha_actual = timezone.now().date()
        
        # Últimos 2 meses
        ventas_recientes = DetalleVenta.objects.filter(
            variante_producto__producto_id=producto_id,
            venta__fecha__gte=fecha_actual - timedelta(days=60)
        ).aggregate(total=Sum('sub_total'))['total'] or 0
        
        # 2 meses anteriores
        ventas_anteriores = DetalleVenta.objects.filter(
            variante_producto__producto_id=producto_id,
            venta__fecha__gte=fecha_actual - timedelta(days=120),
            venta__fecha__lt=fecha_actual - timedelta(days=60)
        ).aggregate(total=Sum('sub_total'))['total'] or 0
        
        if ventas_anteriores > 0:
            return (float(ventas_recientes) - float(ventas_anteriores)) / float(ventas_anteriores)
        
        return 0.0
