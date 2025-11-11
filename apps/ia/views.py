from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import ModeloEntrenamiento, AlertaAnomalia
from .serializers import (
    ModeloEntrenamientoSerializer,
    AlertaAnomaliaSerializer,
    PrediccionGeneralSerializer,
    PrediccionProductoSerializer,
    MetricasModeloSerializer
)
from .services import MLService, Predictor, AnomalyDetector


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predict_general(request):
    try:
        periodo = request.query_params.get('periodo', 'semanal')
        cantidad = int(request.query_params.get('cantidad', 4))
        
        if periodo not in ['semanal', 'mensual']:
            return Response(
                {'error': "El período debe ser 'semanal' o 'mensual'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cantidad < 1 or cantidad > 12:
            return Response(
                {'error': 'La cantidad debe estar entre 1 y 12'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Realizar predicción
        predictor = Predictor()
        predicciones = predictor.predecir_ventas_generales(
            periodo=periodo,
            cantidad_periodos=cantidad
        )
        
        serializer = PrediccionGeneralSerializer(predicciones, many=True)
        
        return Response({
            'success': True,
            'periodo': periodo,
            'cantidad_periodos': cantidad,
            'fecha_prediccion': timezone.now(),
            'predicciones': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predict_product(request, producto_id):
    try:
        periodo = request.query_params.get('periodo', 'mensual')
        cantidad = int(request.query_params.get('cantidad', 3))
        
        if periodo not in ['semanal', 'mensual']:
            return Response(
                {'error': "El período debe ser 'semanal' o 'mensual'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Realizar predicción
        predictor = Predictor()
        predicciones = predictor.predecir_ventas_producto(
            producto_id=producto_id,
            periodo=periodo,
            cantidad_periodos=cantidad
        )
        
        serializer = PrediccionProductoSerializer(predicciones, many=True)
        
        return Response({
            'success': True,
            'producto_id': producto_id,
            'periodo': periodo,
            'cantidad_periodos': cantidad,
            'fecha_prediccion': timezone.now(),
            'predicciones': serializer.data
        })
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alerts(request):
    try:
        estado_param = request.query_params.get('estado')
        limite = int(request.query_params.get('limite', 20))
        
        # Obtener alertas
        queryset = AlertaAnomalia.objects.all()
        
        if estado_param:
            queryset = queryset.filter(estado=estado_param)
        else:
            # Por defecto, solo alertas activas
            queryset = queryset.filter(estado__in=['nueva', 'revisada'])
        
        alertas = queryset.order_by('-fecha_deteccion')[:limite]
        
        serializer = AlertaAnomaliaSerializer(alertas, many=True)
        
        return Response({
            'success': True,
            'cantidad': len(alertas),
            'alertas': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_anomalies(request):
    try:
        dias_analisis = request.data.get('dias_analisis', 30)
        
        # Ejecutar detección
        detector = AnomalyDetector()
        alertas = detector.detectar_anomalias(dias_analisis=dias_analisis)
        
        serializer = AlertaAnomaliaSerializer(alertas, many=True)
        
        return Response({
            'success': True,
            'mensaje': f'Detección completada. {len(alertas)} nuevas anomalías detectadas',
            'cantidad_detectadas': len(alertas),
            'alertas': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_model(request):
    try:
        # Verificar permisos de administrador
        if not request.user.is_staff and request.user.rol != 'administrador':
            return Response(
                {'error': 'No tienes permisos para entrenar el modelo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Iniciar entrenamiento
        ml_service = MLService()
        resultado = ml_service.entrenar()
        
        if resultado['success']:
            return Response({
                'success': True,
                'mensaje': 'Modelo entrenado exitosamente',
                'modelo_id': resultado['modelo_id'],
                'version': resultado['version'],
                'metricas': {
                    'mae': resultado['metricas']['mae'],
                    'mse': resultado['metricas']['mse'],
                    'r2_score': resultado['metricas']['r2'],
                    'registros_entrenamiento': resultado['metricas']['registros_train'],
                    'registros_prueba': resultado['metricas']['registros_test'],
                },
                'archivo_modelo': resultado['archivo']
            })
        else:
            return Response(
                {'error': resultado['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def model_info(request):
    try:
        ml_service = MLService()
        metricas = ml_service.obtener_metricas_modelo_activo()
        
        if metricas:
            serializer = MetricasModeloSerializer(metricas)
            return Response({
                'success': True,
                'modelo_activo': True,
                'metricas': serializer.data
            })
        else:
            return Response({
                'success': True,
                'modelo_activo': False,
                'mensaje': 'No hay modelo entrenado. Usa POST /api/ia/train para entrenar uno.'
            })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def training_history(request):
    try:
        limite = int(request.query_params.get('limite', 10))
        
        modelos = ModeloEntrenamiento.objects.all()[:limite]
        serializer = ModeloEntrenamientoSerializer(modelos, many=True)
        
        return Response({
            'success': True,
            'cantidad': len(modelos),
            'entrenamientos': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_alert(request, alerta_id):
    try:
        alerta = AlertaAnomalia.objects.get(id=alerta_id)
        
        nuevo_estado = request.data.get('estado')
        nota = request.data.get('nota_resolucion')
        
        if nuevo_estado:
            if nuevo_estado not in ['revisada', 'resuelta', 'ignorada']:
                return Response(
                    {'error': 'Estado inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            alerta.estado = nuevo_estado
        
        if nota:
            alerta.nota_resolucion = nota
        
        alerta.save()
        
        serializer = AlertaAnomaliaSerializer(alerta)
        
        return Response({
            'success': True,
            'mensaje': 'Alerta actualizada',
            'alerta': serializer.data
        })
        
    except AlertaAnomalia.DoesNotExist:
        return Response(
            {'error': 'Alerta no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
