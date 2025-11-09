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
    def crear_venta(
        vendedor_id, 
        items, 
        tipo_venta, 
        cliente_id=None, 
        interes=None, 
        plazo_meses=None,
        correo_cliente=None,
        direccion_cliente=None,
        nombre_cliente=None,
        telefono_cliente=None,
        numero_cliente=None,
        estado='pendiente'
    ):
        """
        Crea una venta completa con sus detalles, reducción de stock y cuotas
        """
        # Validar vendedor
        print("👤 Validando vendedor...")
        try:
            vendedor = Usuario.objects.get(id=vendedor_id)
            if vendedor.rol != 'vendedor':
                raise ValueError(f"El usuario {vendedor.username} debe tener rol 'vendedor'")
            if not vendedor.activo:
                raise ValueError(f"El vendedor {vendedor.username} no está activo")
        except Usuario.DoesNotExist:
            raise ValueError(f"Vendedor con ID {vendedor_id} no existe")
        
        print(f"   ✓ Vendedor: {vendedor.username}")
        
        print("🔍 Validando stock...")
        for item in items:
            try:
                variante = VarianteProducto.objects.select_for_update().get(
                    id=item['variante_id']
                )
            except VarianteProducto.DoesNotExist:
                raise ValueError(f"Variante con ID {item['variante_id']} no existe")

            if variante.stock < item['cantidad']:
                talla_info = f" - Talla {variante.talla}" if variante.talla else ""
                raise ValueError(
                    f"Stock insuficiente para {variante.producto.nombre}{talla_info}. "
                    f"Disponible: {variante.stock}, Solicitado: {item['cantidad']}"
                )

        print("💰 Calculando totales...")
        subtotal_total = Decimal('0.00')
        detalles_data = []

        for item in items:
            variante = VarianteProducto.objects.get(id=item['variante_id'])
            cantidad = item['cantidad']
            precio_unitario = Decimal(str(variante.precio))
            sub_total = precio_unitario * cantidad

            subtotal_total += sub_total

            detalles_data.append({
                'variante': variante,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'sub_total': sub_total,
                # Snapshot de datos (por si cambian después)
                'nombre_producto': variante.producto.nombre,
                'talla': variante.talla
            })

        print(f"   Subtotal: {subtotal_total}")

        total_con_interes = subtotal_total
        cuota_mensual = Decimal('0.00')

        if tipo_venta == 'credito':
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
                if cliente.rol != 'cliente':
                    raise ValueError(f"El usuario {cliente.username} debe tener rol 'cliente'")
                print(f"👤 Cliente registrado: {cliente.email}")
            except Usuario.DoesNotExist:
                raise ValueError(f"Cliente con ID {cliente_id} no existe")
        else:
            print("👤 Venta sin cliente registrado (datos manuales)")

        print("📝 Creando venta...")
        venta = Venta.objects.create(
            cliente=cliente,
            vendedor=vendedor,
            nombre_vendedor=vendedor.get_full_name() or vendedor.username,
            correo_cliente=correo_cliente,
            direccion_cliente=direccion_cliente,
            nombre_cliente=nombre_cliente,
            telefono_cliente=telefono_cliente,
            numero_cliente=numero_cliente,
            estado=estado,
            tipo_venta=tipo_venta,
            total=subtotal_total,
            total_con_interes=total_con_interes,
            plazo_meses=plazo_meses if tipo_venta == 'credito' else None,
            interes=interes if tipo_venta == 'credito' else None,
            cuota_mensual=cuota_mensual
        )

        print(f"✅ Venta #{venta.pk} creada")

        
        print("📦 Creando detalles y reduciendo stock...")
        for detalle_data in detalles_data:
            # Crear detalle
            DetalleVenta.objects.create(
                venta=venta,
                variante_producto=detalle_data['variante'],
                cantidad=detalle_data['cantidad'],
                precio_unitario=detalle_data['precio_unitario'],
                sub_total=detalle_data['sub_total'],
                nombre_producto=detalle_data['nombre_producto'],
                talla=detalle_data['talla']
            )

            # REDUCIR STOCK
            variante = detalle_data['variante']
            stock_anterior = variante.stock
            variante.stock -= detalle_data['cantidad']
            variante.save()

            talla_info = f" - Talla {detalle_data['talla']}" if detalle_data['talla'] else ""
            print(f"   ✓ {detalle_data['nombre_producto']}{talla_info} x{detalle_data['cantidad']} "
                  f"(Stock: {stock_anterior} → {variante.stock})")

        if tipo_venta == 'credito':
            print("📅 Creando cuotas...")
            VentaService._crear_cuotas(venta, plazo_meses, cuota_mensual)

        print(f"🎉 Venta #{venta.pk} completada exitosamente")
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

