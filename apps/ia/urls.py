"""
URLs del módulo de Inteligencia Artificial
"""
from django.urls import path
from . import views

app_name = 'ia'

urlpatterns = [
    # Predicciones
    path('predict-general/', views.predict_general, name='predict-general'),
    path('predict-product/<int:producto_id>/', views.predict_product, name='predict-product'),
    
    # Alertas y Anomalías
    path('alerts/', views.alerts, name='alerts'),
    path('alerts/<int:alerta_id>/', views.update_alert, name='update-alert'),
    path('detect-anomalies/', views.detect_anomalies, name='detect-anomalies'),
    
    # Modelo
    path('train/', views.train_model, name='train'),
    path('model-info/', views.model_info, name='model-info'),
    path('training-history/', views.training_history, name='training-history'),
]
