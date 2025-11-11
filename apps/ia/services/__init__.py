# apps/ia/services/__init__.py
from .ml_service import MLService
from .predictor import Predictor
from .anomaly_detector import AnomalyDetector

__all__ = ['MLService', 'Predictor', 'AnomalyDetector']
