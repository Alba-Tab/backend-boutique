"""
Script de prueba rápida para el sistema de reportes

Ejecutar con: python manage.py shell < apps/reports/test_reportes.py
O desde shell: python manage.py shell
>>> exec(open('apps/reports/test_reportes.py').read())
"""

print("=" * 60)
print("🧪 PRUEBAS DEL SISTEMA DE REPORTES")
print("=" * 60)

from apps.reports.services import ventas_report_service
from apps.reports.services import products_report_service
from apps.reports.services import pagos_report_service
from datetime import datetime, timedelta

print("\n📊 1. REPORTE DE VENTAS")
print("-" * 60)
try:
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    ventas = ventas_report_service.report_ventas({
        'fecha_inicio': str(hace_30_dias),
        'fecha_fin': str(hoy)
    })
    
    print(f"✅ Summary: {ventas['summary']}")
    print(f"✅ Total ventas: Bs. {ventas['meta']['total_ventas']}")
    print(f"✅ Cantidad: {ventas['meta']['cantidad_ventas']}")
    print(f"✅ Promedio: Bs. {ventas['meta']['promedio_venta']}")
    print(f"✅ Productos vendidos: {len(ventas['rows'])}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📦 2. REPORTE DE PRODUCTOS")
print("-" * 60)
try:
    productos = products_report_service.report_productos({})
    
    print(f"✅ Summary: {productos['summary']}")
    print(f"✅ Total variantes: {productos['meta']['total_variantes']}")
    print(f"✅ Total stock: {productos['meta']['total_stock']}")
    print(f"✅ Total vendidos: {productos['meta']['total_vendidos']}")
    print(f"✅ Productos críticos: {productos['meta']['productos_criticos']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n⚠️ 3. STOCK BAJO")
print("-" * 60)
try:
    stock = products_report_service.report_stock_bajo()
    
    print(f"✅ Summary: {stock['summary']}")
    print(f"✅ Total productos críticos: {stock['meta']['total_productos_criticos']}")
    print(f"✅ Sin stock: {stock['meta']['sin_stock']}")
    
    if stock['rows']:
        print("\n🔴 Productos con stock bajo:")
        for p in stock['rows'][:5]:  # Mostrar solo los primeros 5
            print(f"   - {p['producto']} ({p['talla']}/{p['color']}): "
                  f"Stock: {p['stock_actual']}/{p['stock_minimo']} - {p['estado']}")
    else:
        print("✅ No hay productos con stock bajo")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🏆 4. PRODUCTOS MÁS VENDIDOS")
print("-" * 60)
try:
    mas_vendidos = products_report_service.report_productos_mas_vendidos(5)
    
    print(f"✅ Summary: {mas_vendidos['summary']}")
    
    if mas_vendidos['rows']:
        print("\n🥇 Top 5 productos:")
        for i, p in enumerate(mas_vendidos['rows'], 1):
            print(f"   {i}. {p['producto']} ({p['talla']}/{p['color']}): "
                  f"{p['cantidad_vendida']} unidades - Bs. {p['ingresos']}")
    else:
        print("⚠️ No hay datos de productos vendidos")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n💰 5. REPORTE DE PAGOS")
print("-" * 60)
try:
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    pagos = pagos_report_service.report_pagos({
        'fecha_inicio': str(hace_30_dias),
        'fecha_fin': str(hoy)
    })
    
    print(f"✅ Summary: {pagos['summary']}")
    print(f"✅ Total pagos: Bs. {pagos['meta']['total_pagos']}")
    print(f"✅ Cantidad: {pagos['meta']['cantidad_pagos']}")
    print(f"✅ Promedio: Bs. {pagos['meta']['promedio_pago']}")
    
    if pagos['rows']:
        print("\n💳 Por método de pago:")
        for m in pagos['rows']:
            print(f"   - {m['método_pago']}: {m['cantidad_pagos']} pagos - Bs. {m['monto_total']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📅 6. REPORTE DE CUOTAS")
print("-" * 60)
try:
    cuotas = pagos_report_service.report_cuotas({})
    
    print(f"✅ Summary: {cuotas['summary']}")
    print(f"✅ Total monto: Bs. {cuotas['meta']['total_monto']}")
    print(f"✅ Cantidad cuotas: {cuotas['meta']['cantidad_cuotas']}")
    print(f"✅ Cuotas vencidas: {cuotas['meta']['cuotas_vencidas']}")
    
    if cuotas['rows']:
        print("\n📊 Por estado:")
        for c in cuotas['rows']:
            print(f"   - {c['estado']}: {c['cantidad_cuotas']} cuotas - Bs. {c['monto_total']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🚨 7. MOROSIDAD")
print("-" * 60)
try:
    morosidad = pagos_report_service.report_morosidad()
    
    print(f"✅ Summary: {morosidad['summary']}")
    print(f"✅ Total cuotas vencidas: {morosidad['meta']['total_cuotas_vencidas']}")
    print(f"✅ Total monto vencido: Bs. {morosidad['meta']['total_monto_vencido']}")
    
    if morosidad['rows']:
        print("\n⚠️ Clientes con deuda:")
        for c in morosidad['rows'][:5]:  # Mostrar solo los primeros 5
            print(f"   - {c['cliente']} ({c['email']}): "
                  f"{c['cuotas_vencidas']} cuotas - Bs. {c['monto_vencido']}")
    else:
        print("✅ No hay clientes con cuotas vencidas")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n💵 8. FLUJO DE CAJA")
print("-" * 60)
try:
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    flujo = pagos_report_service.report_flujo_caja({
        'fecha_inicio': str(hace_30_dias),
        'fecha_fin': str(hoy)
    })
    
    print(f"✅ Summary: {flujo['summary']}")
    print(f"✅ Ingresos reales: Bs. {flujo['meta']['ingresos_reales']}")
    print(f"✅ Por cobrar: Bs. {flujo['meta']['por_cobrar']}")
    print(f"✅ Efectividad cobranza: {flujo['meta']['efectividad_cobranza']}%")
    
    if flujo['rows']:
        print("\n📊 Detalle:")
        for f in flujo['rows']:
            print(f"   - {f['concepto']}: Bs. {f['monto']}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n💎 9. RENTABILIDAD")
print("-" * 60)
try:
    rentabilidad = products_report_service.report_rentabilidad_productos()
    
    print(f"✅ Summary: {rentabilidad['summary']}")
    print(f"✅ Total ingresos: Bs. {rentabilidad['meta']['total_ingresos']}")
    print(f"✅ Total costos: Bs. {rentabilidad['meta']['total_costos']}")
    print(f"✅ Ganancia total: Bs. {rentabilidad['meta']['ganancia_total']}")
    print(f"✅ Margen promedio: {rentabilidad['meta']['margen_promedio']}%")
    
    if rentabilidad['rows']:
        print("\n💰 Top 5 más rentables:")
        for i, p in enumerate(rentabilidad['rows'][:5], 1):
            print(f"   {i}. {p['producto']}: "
                  f"Ganancia Bs. {p['ganancia_neta']} - Margen {p['margen_porcentaje']}%")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ PRUEBAS COMPLETADAS")
print("=" * 60)
print("\n💡 Siguiente paso: Probar los endpoints API")
print("   GET  http://localhost:8000/api/v1/reports/dashboard/")
print("   GET  http://localhost:8000/api/v1/reports/cierre-dia/")
print("   GET  http://localhost:8000/api/v1/reports/alertas-inventario/")
print("   POST http://localhost:8000/api/v1/reports/generate/")
