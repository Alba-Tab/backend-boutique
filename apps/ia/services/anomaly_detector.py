import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from apps.venta.models import Venta, DetalleVenta
from apps.productos.models import Producto
from apps.ia.models import AlertaAnomalia
from .ml_service import MLService


class AnomalyDetector:
    
    def __init__(self):
        self.ml_service = MLService()
        self.ml_service.cargar_modelos()
    
    def detectar_anomalias(self, dias_analisis=30):
        
        fecha_inicio = timezone.now().date() - timedelta(days=dias_analisis)
        alertas = []
        
        alertas_diarias = self._detectar_anomalias_diarias(fecha_inicio)
        alertas.extend(alertas_diarias)
        
        alertas_productos = self._detectar_anomalias_productos(fecha_inicio)
        alertas.extend(alertas_productos)
        
        alertas_tendencias = self._detectar_tendencias_negativas(fecha_inicio)
        alertas.extend(alertas_tendencias)
        
        return alertas
    
    def _detectar_anomalias_diarias(self, fecha_inicio):
        
        alertas = []
        
        # Obtener ventas por día
        ventas_diarias = Venta.objects.filter(
            fecha__gte=fecha_inicio
        ).values('fecha').annotate(
            total_dia=Sum('total'),
            cantidad_ventas=Count('id')
        ).order_by('fecha')
        
        if len(ventas_diarias) < 7:
            return alertas 
        
        totales = [float(v['total_dia']) for v in ventas_diarias]
        media = np.mean(totales)
        std = np.std(totales)
        
        # Detectar outliers usando Z-score (> 2 std)
        for venta_dia in ventas_diarias:
            total = float(venta_dia['total_dia'])
            z_score = (total - media) / std if std > 0 else 0
            
            if abs(z_score) > 2:
                # Es una anomalía
                tipo = 'venta_alta' if z_score > 0 else 'venta_baja'
                
                # Verificar si ya existe esta alerta
                existe = AlertaAnomalia.objects.filter(
                    fecha_referencia=venta_dia['fecha'],
                    tipo=tipo,
                    estado__in=['nueva', 'revisada']
                ).exists()
                
                if not existe:
                    alerta = AlertaAnomalia.objects.create(
                        tipo=tipo,
                        fecha_referencia=venta_dia['fecha'],
                        descripcion=f"Ventas {'inusualmente altas' if tipo == 'venta_alta' else 'inusualmente bajas'} "
                                   f"detectadas: Bs. {total:.2f} (promedio: Bs. {media:.2f})",
                        score_anomalia=-1 if abs(z_score) > 2 else 1,
                        valor_real=Decimal(str(round(total, 2))),
                        valor_esperado=Decimal(str(round(media, 2))),
                        estado='nueva'
                    )
                    alertas.append(alerta)
        
        return alertas
    
    def _detectar_anomalias_productos(self, fecha_inicio):
        
        alertas = []
        
        productos_vendidos = DetalleVenta.objects.filter(
            venta__fecha__gte=fecha_inicio
        ).values('variante_producto__producto').distinct()
        
        for prod in productos_vendidos:
            producto_id = prod['variante_producto__producto']
            
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                continue
            
            ventas_producto = DetalleVenta.objects.filter(
                variante_producto__producto_id=producto_id,
                venta__fecha__gte=fecha_inicio
            ).values('venta__fecha').annotate(
                total=Sum('sub_total'),
                cantidad=Sum('cantidad')
            )
            
            if len(ventas_producto) < 5:
                continue
            
            totales = [float(v['total']) for v in ventas_producto]
            media = np.mean(totales)
            std = np.std(totales)
            
            for venta in ventas_producto:
                total = float(venta['total'])
                z_score = (total - media) / std if std > 0 else 0
                
                if abs(z_score) > 2.5:  # Umbral más alto para productos
                    # Verificar si ya existe
                    existe = AlertaAnomalia.objects.filter(
                        fecha_referencia=venta['venta__fecha'],
                        producto_id=producto_id,
                        tipo='producto_anomalo',
                        estado__in=['nueva', 'revisada']
                    ).exists()
                    
                    if not existe:
                        alerta = AlertaAnomalia.objects.create(
                            tipo='producto_anomalo',
                            fecha_referencia=venta['venta__fecha'],
                            descripcion=f"Comportamiento anómalo en producto '{producto.nombre}': "
                                       f"ventas {'muy altas' if z_score > 0 else 'muy bajas'} - "
                                       f"Bs. {total:.2f} (esperado: Bs. {media:.2f})",
                            score_anomalia=-1,
                            producto_id=producto_id,
                            producto_nombre=producto.nombre,
                            valor_real=Decimal(str(round(total, 2))),
                            valor_esperado=Decimal(str(round(media, 2))),
                            estado='nueva'
                        )
                        alertas.append(alerta)
        
        return alertas
    
    def _detectar_tendencias_negativas(self, fecha_inicio):
        
        alertas = []
        
        # Dividir el período en dos mitades
        punto_medio = fecha_inicio + (timezone.now().date() - fecha_inicio) / 2
        
        # Ventas primera mitad
        ventas_primera_mitad = Venta.objects.filter(
            fecha__gte=fecha_inicio,
            fecha__lt=punto_medio
        ).aggregate(total=Sum('total'))['total'] or 0
        
        # Ventas segunda mitad
        ventas_segunda_mitad = Venta.objects.filter(
            fecha__gte=punto_medio
        ).aggregate(total=Sum('total'))['total'] or 0
        
        if ventas_primera_mitad > 0:
            cambio_porcentual = (
                (float(ventas_segunda_mitad) - float(ventas_primera_mitad)) 
                / float(ventas_primera_mitad)
            ) * 100
            
            # Si hay caída mayor al 20%
            if cambio_porcentual < -20:
                existe = AlertaAnomalia.objects.filter(
                    fecha_referencia=timezone.now().date(),
                    tipo='tendencia_negativa',
                    estado__in=['nueva', 'revisada']
                ).exists()
                
                if not existe:
                    alerta = AlertaAnomalia.objects.create(
                        tipo='tendencia_negativa',
                        fecha_referencia=timezone.now().date(),
                        descripcion=f"Tendencia negativa detectada: caída del {abs(cambio_porcentual):.1f}% "
                                   f"en ventas comparando períodos recientes",
                        score_anomalia=-1,
                        valor_real=Decimal(str(round(float(ventas_segunda_mitad), 2))),
                        valor_esperado=Decimal(str(round(float(ventas_primera_mitad), 2))),
                        estado='nueva'
                    )
                    alertas.append(alerta)
        
        return alertas
    
    def obtener_alertas_activas(self, limite=20):
        
        return AlertaAnomalia.objects.filter(
            estado__in=['nueva', 'revisada']
        ).order_by('-fecha_deteccion')[:limite]
    
    def marcar_alerta_resuelta(self, alerta_id, nota=None):
        try:
            alerta = AlertaAnomalia.objects.get(id=alerta_id)
            alerta.estado = 'resuelta'
            if nota:
                alerta.nota_resolucion = nota
            alerta.save()
            return True
        except AlertaAnomalia.DoesNotExist:
            return False
