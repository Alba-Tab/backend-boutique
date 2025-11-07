from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from apps.cuota.models import CuotaCredito

from .models import Venta, DetalleVenta
from apps.producto_variante.models import VarianteProducto
from apps.usuarios.models import Usuario


class VentaService:
    
    @staticmethod
    @transaction.atomic
    def crear_venta(cliente_id, items, tipo_pago, interes=None, plazo_meses=None):
        """
        Crea una venta completa con sus detalles, reducción de stock y cuotas

        """
        print("🔍 Validando stock...")
        for item in items:
            try:
                variante = VarianteProducto.objects.select_for_update().get(
                    id=item['variante_id']
                )
            except VarianteProducto.DoesNotExist:
                raise ValueError(f"Variante con ID {item['variante_id']} no existe")

            if variante.stock < item['cantidad']:
                raise ValueError(
                    f"Stock insuficiente para {variante.producto.nombre} "
                    f"({variante.talla} - {variante.color}). "
                    f"Disponible: {variante.stock}, Solicitado: {item['cantidad']}"
                )

        print("💰 Calculando totales...")
        subtotal_total = Decimal('0.00')
        detalles_data = []

        for item in items:
            variante = VarianteProducto.objects.get(id=item['variante_id'])
            cantidad = item['cantidad']
            precio_unitario = Decimal(str(variante.precio_venta))
            subtotal = precio_unitario * cantidad

            subtotal_total += subtotal

            detalles_data.append({
                'variante': variante,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal,
                # Snapshot de datos (por si cambian después)
                'producto_nombre': variante.producto.nombre,
                'talla': variante.talla,
                'color': variante.color
            })

        print(f"   Subtotal: {subtotal_total}")

        total_con_interes = None
        cuota_mensual = None

        if tipo_pago == 'credito':
            print("🏦 Calculando crédito...")

            if not interes or not plazo_meses:
                raise ValueError(
                    "Ventas a crédito requieren 'interes' y 'plazo_meses'"
                )

            interes_decimal = Decimal(str(interes))
            # Calcular el monto del interés
            interes_monto = subtotal_total * (interes_decimal / Decimal('100'))
            # Total con interés = subtotal + interés
            total_con_interes = subtotal_total + interes_monto
            # Cuota mensual = total con interés / meses
            cuota_mensual = total_con_interes / Decimal(str(plazo_meses))

            print(f"   Interés: {interes}% = {interes_monto}")
            print(f"   Total con interés: {total_con_interes}")
            print(f"   Cuota mensual: {cuota_mensual}")

        cliente = None
        if cliente_id:
            try:
                cliente = Usuario.objects.get(id=cliente_id)
                print(f"👤 Cliente: {cliente.email}")
            except Usuario.DoesNotExist:
                raise ValueError(f"Cliente con ID {cliente_id} no existe")
        else:
            print("👤 Venta sin cliente registrado (anónimo)")

        print("📝 Creando venta...")
        venta = Venta.objects.create(
            cliente=cliente,  # ⬅️ Puede ser None
            total=subtotal_total,  # Total SIN interés (base)
            tipo_pago=tipo_pago,
            estado_pago='pendiente',
            interes=interes if tipo_pago == 'credito' else None,
            total_con_interes=total_con_interes,  # Total CON interés (solo crédito)
            plazo_meses=plazo_meses if tipo_pago == 'credito' else None,
            cuota_mensual=cuota_mensual
        )

        print(f"✅ Venta #{venta.id} creada")

        
        print("📦 Creando detalles y reduciendo stock...")
        for detalle_data in detalles_data:
            # Crear detalle
            DetalleVenta.objects.create(
                venta=venta,
                variante=detalle_data['variante'],
                cantidad=detalle_data['cantidad'],
                precio_unitario=detalle_data['precio_unitario'],
                subtotal=detalle_data['subtotal'],
                producto_nombre=detalle_data['producto_nombre'],
                talla=detalle_data['talla'],
                color=detalle_data['color']
            )

            # REDUCIR STOCK
            variante = detalle_data['variante']
            stock_anterior = variante.stock
            variante.stock -= detalle_data['cantidad']
            variante.save()

            print(f"   ✓ {detalle_data['producto_nombre']} x{detalle_data['cantidad']} "
                  f"(Stock: {stock_anterior} → {variante.stock})")

        if tipo_pago == 'credito':
            print("📅 Creando cuotas...")
            VentaService._crear_cuotas(venta, plazo_meses, cuota_mensual)

        print(f"🎉 Venta #{venta.id} completada exitosamente")
        return venta


    @staticmethod
    def _crear_cuotas(venta, plazo_meses, cuota_mensual):
        """
        Crea las cuotas mensuales para una venta a crédito

        Args:
            venta (Venta): Instancia de la venta
            plazo_meses (int): Número de cuotas a crear
            cuota_mensual (Decimal): Monto de cada cuota
        """
        fecha_base = timezone.now().date()

        for numero in range(1, plazo_meses + 1):
            # Vencimiento: cada 30 días
            fecha_vencimiento = fecha_base + timedelta(days=30 * numero)

            cuota = CuotaCredito.objects.create(
                venta=venta,
                numero_cuota=numero,
                fecha_vencimiento=fecha_vencimiento,
                monto_cuota=cuota_mensual,
                estado='pendiente'
            )

            print(f"   ✓ Cuota {numero}/{plazo_meses} - "
                  f"Vence: {fecha_vencimiento} - "
                  f"Monto: {cuota_mensual}")

