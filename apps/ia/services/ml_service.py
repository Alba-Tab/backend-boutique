import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone

from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

from apps.venta.models import Venta, DetalleVenta
from apps.productos.models import Producto
from apps.ia.models import ModeloEntrenamiento, AlertaAnomalia


class MLService:
    
    def __init__(self):
        self.model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        self.modelo_ventas = None
        self.modelo_anomalias = None
        self.label_encoders = {}
        
        # Crear directorio si no existe
        os.makedirs(self.model_dir, exist_ok=True)
        
    def cargar_modelos(self):
        try:
            ultimo_modelo = ModeloEntrenamiento.objects.filter(activo=True).first()
            
            if ultimo_modelo:
                modelo_path = os.path.join(self.model_dir, ultimo_modelo.archivo_modelo)
                if os.path.exists(modelo_path):
                    modelos_data = joblib.load(modelo_path)
                    self.modelo_ventas = modelos_data.get('modelo_ventas')
                    self.modelo_anomalias = modelos_data.get('modelo_anomalias')
                    self.label_encoders = modelos_data.get('label_encoders', {})
                    print(f"✅ Modelos cargados: {ultimo_modelo.archivo_modelo}")
                    return True
            
            print("⚠️ No hay modelos entrenados disponibles")
            return False
            
        except Exception as e:
            print(f"❌ Error al cargar modelos: {str(e)}")
            return False
    
    def preparar_datos_entrenamiento(self):
        ventas = Venta.objects.filter(
            fecha__gte=timezone.now().date() - timedelta(days=365)
        ).select_related('cliente', 'vendedor').prefetch_related('detalles')
        
        datos = []
        
        for venta in ventas:
            fecha = venta.fecha
            
            anio = fecha.year
            mes = fecha.month
            dia_semana = fecha.weekday()
            semana_anio = fecha.isocalendar()[1]
            es_fin_semana = 1 if dia_semana >= 5 else 0
            
            total_venta = float(venta.total)
            tipo_venta = venta.tipo_venta
            origen = venta.origen
            
            cantidad_productos = venta.detalles.count()
            cantidad_productos = venta.detalles.count()
            
            # Por cada detalle, crear registro para predicción por producto
            for detalle in venta.detalles.all():
                datos.append({
                    'fecha': fecha,
                    'anio': anio,
                    'mes': mes,
                    'dia_semana': dia_semana,
                    'semana_anio': semana_anio,
                    'es_fin_semana': es_fin_semana,
                    'tipo_venta': tipo_venta,
                    'origen': origen,
                    'producto_id': detalle.variante_producto.producto.id,
                    'producto_nombre': detalle.nombre_producto,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'sub_total': float(detalle.sub_total),
                    'total_venta': total_venta,
                    'cantidad_productos_venta': cantidad_productos,
                })
        
        if not datos:
            raise ValueError("No hay datos suficientes para entrenar el modelo")
        
        df = pd.DataFrame(datos)
        
        # Agregar features de tendencia (promedios móviles)
        df = df.sort_values('fecha')
        df['promedio_movil_7d'] = df.groupby('producto_id')['sub_total'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        df['promedio_movil_30d'] = df.groupby('producto_id')['sub_total'].transform(
            lambda x: x.rolling(window=30, min_periods=1).mean()
        )
        
        return df
    
    def entrenar_modelo_ventas(self, df):
        """
        Entrena el modelo de predicción de ventas (RandomForest)
        """
        # Codificar variables categóricas
        self.label_encoders = {}
        df_encoded = df.copy()
        
        for col in ['tipo_venta', 'origen']:
            le = LabelEncoder()
            df_encoded[col + '_encoded'] = le.fit_transform(df_encoded[col])
            self.label_encoders[col] = le
        
        # Features para el modelo
        feature_columns = [
            'anio', 'mes', 'dia_semana', 'semana_anio', 'es_fin_semana',
            'tipo_venta_encoded', 'origen_encoded', 'producto_id',
            'precio_unitario', 'cantidad_productos_venta',
            'promedio_movil_7d', 'promedio_movil_30d'
        ]
        
        X = df_encoded[feature_columns]
        y = df_encoded['sub_total']  # Variable objetivo: ventas
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Entrenar modelo
        self.modelo_ventas = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.modelo_ventas.fit(X_train, y_train)
        
        # Calcular métricas
        y_pred = self.modelo_ventas.predict(X_test)
        
        metricas = {
            'mae': mean_absolute_error(y_test, y_pred),
            'mse': mean_squared_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred),
            'registros_train': len(X_train),
            'registros_test': len(X_test),
        }
        
        return metricas
    
    def entrenar_modelo_anomalias(self, df):
        """
        Entrena el modelo de detección de anomalías (IsolationForest)
        """
        # Agrupar ventas por día para detectar patrones anómalos
        df_daily = df.groupby(['fecha', 'producto_id']).agg({
            'sub_total': 'sum',
            'cantidad': 'sum'
        }).reset_index()
        
        # Features para detección de anomalías
        features_anomalias = df_daily[['sub_total', 'cantidad']].values
        
        # Entrenar IsolationForest
        self.modelo_anomalias = IsolationForest(
            contamination=0.1,  # 10% de datos considerados anómalos
            random_state=42,
            n_jobs=-1
        )
        
        self.modelo_anomalias.fit(features_anomalias)
        
        return True
    
    def entrenar(self):
        try:
            print("🚀 Iniciando entrenamiento de modelos ML...")
            
            # 1. Preparar datos
            print("📊 Preparando datos de entrenamiento...")
            df = self.preparar_datos_entrenamiento()
            print(f"✅ {len(df)} registros preparados")
            
            # 2. Entrenar modelo de predicción
            print("🤖 Entrenando modelo de predicción de ventas...")
            metricas = self.entrenar_modelo_ventas(df)
            print(f"✅ Modelo entrenado - MAE: {metricas['mae']:.2f}, R²: {metricas['r2']:.4f}")
            
            # 3. Entrenar modelo de anomalías
            print("🔍 Entrenando modelo de detección de anomalías...")
            self.entrenar_modelo_anomalias(df)
            print("✅ Modelo de anomalías entrenado")
            
            # 4. Guardar modelos
            version = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f'modelo_ventas_{version}.pkl'
            ruta_completa = os.path.join(self.model_dir, nombre_archivo)
            
            modelos_data = {
                'modelo_ventas': self.modelo_ventas,
                'modelo_anomalias': self.modelo_anomalias,
                'label_encoders': self.label_encoders,
                'version': version,
                'fecha_entrenamiento': datetime.now(),
            }
            
            joblib.dump(modelos_data, ruta_completa)
            print(f"💾 Modelos guardados en: {nombre_archivo}")
            
            # 5. Registrar en base de datos
            # Desactivar modelos anteriores
            ModeloEntrenamiento.objects.filter(activo=True).update(activo=False)
            
            # Crear nuevo registro
            modelo_db = ModeloEntrenamiento.objects.create(
                nombre='modelo_ventas',
                version=version,
                mae=metricas['mae'],
                mse=metricas['mse'],
                r2_score=metricas['r2'],
                registros_entrenamiento=metricas['registros_train'],
                registros_prueba=metricas['registros_test'],
                archivo_modelo=nombre_archivo,
                activo=True,
                notas=f"Entrenamiento automático con {len(df)} registros históricos"
            )
            
            print("✅ Entrenamiento completado exitosamente")
            
            return {
                'success': True,
                'metricas': metricas,
                'modelo_id': modelo_db.id,
                'version': version,
                'archivo': nombre_archivo,
            }
            
        except Exception as e:
            print(f"❌ Error durante el entrenamiento: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_metricas_modelo_activo(self):
        """
        Obtiene las métricas del modelo activo
        """
        try:
            modelo = ModeloEntrenamiento.objects.filter(activo=True).first()
            
            if not modelo:
                return None
            
            return {
                'mae': modelo.mae,
                'mse': modelo.mse,
                'r2_score': modelo.r2_score,
                'registros_entrenamiento': modelo.registros_entrenamiento,
                'registros_prueba': modelo.registros_prueba,
                'fecha_entrenamiento': modelo.fecha_entrenamiento,
                'version': modelo.version,
            }
        except Exception as e:
            print(f"Error al obtener métricas: {str(e)}")
            return None
