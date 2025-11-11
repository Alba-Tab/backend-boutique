import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ia.services import MLService


def main():
    print("=" * 60)
    print("🤖 INICIALIZACIÓN DEL MÓDULO DE INTELIGENCIA ARTIFICIAL")
    print("=" * 60)
    print()
    
    print("Este script va a:")
    print("  1. Verificar que hay datos suficientes")
    print("  2. Entrenar los modelos de ML")
    print("  3. Guardar los modelos en disco")
    print()
    
    respuesta = input("¿Continuar? (s/n): ")
    
    if respuesta.lower() != 's':
        print("❌ Cancelado por el usuario")
        return
    
    print()
    print("🚀 Iniciando entrenamiento...")
    print()
    
    try:
        ml_service = MLService()
        resultado = ml_service.entrenar()
        
        if resultado['success']:
            print()
            print("=" * 60)
            print("✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
            print("=" * 60)
            print()
            print(f"📊 Métricas del Modelo:")
            print(f"   - MAE (Error Absoluto Medio): {resultado['metricas']['mae']:.2f}")
            print(f"   - MSE (Error Cuadrático Medio): {resultado['metricas']['mse']:.2f}")
            print(f"   - R² Score: {resultado['metricas']['r2']:.4f}")
            print(f"   - Registros de entrenamiento: {resultado['metricas']['registros_train']}")
            print(f"   - Registros de prueba: {resultado['metricas']['registros_test']}")
            print()
            print(f"💾 Modelo guardado: {resultado['archivo']}")
            print(f"🆔 ID del modelo en BD: {resultado['modelo_id']}")
            print(f"📌 Versión: {resultado['version']}")
            print()
            print("🎯 El modelo está listo para realizar predicciones!")
            print()
            print("Prueba los endpoints:")
            print("  - GET /api/ia/predict-general/")
            print("  - GET /api/ia/predict-product/{id}/")
            print("  - GET /api/ia/alerts/")
            print()
        else:
            print()
            print("=" * 60)
            print("❌ ERROR EN EL ENTRENAMIENTO")
            print("=" * 60)
            print()
            print(f"Error: {resultado['error']}")
            print()
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR INESPERADO")
        print("=" * 60)
        print()
        print(f"Error: {str(e)}")
        print()


if __name__ == '__main__':
    main()
