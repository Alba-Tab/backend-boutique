from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Pago
from apps.venta.models import Venta


class PagoService:
    @staticmethod
    @transaction.atomic
    def registrar_pago(venta_id, monto_pagado, metodo_pago, referencia_pago=None, cuota_id=None):
    
        # Registra un pago y actualiza el estado de la venta
        
        try:
            venta = Venta.objects.select_for_update().get(pk=venta_id)
        except Venta.DoesNotExist:
            raise ValueError(f"Venta con ID {venta_id} no existe")

        monto_pagado = Decimal(str(monto_pagado))

        if monto_pagado <= 0:
            raise ValueError("El monto debe ser mayor a 0")

        total_a_pagar = (
            venta.total_con_interes
            if venta.tipo_venta == 'credito' and venta.total_con_interes
            else venta.total
        )

        # Calcular total ya pagado
        total_pagado_anterior = sum(
            Decimal(str(p.monto_pagado)) for p in venta.pagos.all()
        )

        saldo_pendiente = total_a_pagar - total_pagado_anterior
        if monto_pagado > saldo_pendiente:
            raise ValueError(
                f"El pago excede el saldo pendiente. "
                f"Total: {total_a_pagar}, "
                f"Ya pagado: {total_pagado_anterior}, "
                f"Saldo pendiente: {saldo_pendiente}"
            )

        cuota = None
        if cuota_id:
            from apps.cuota.models import CuotaCredito
            
            try:
                cuota = CuotaCredito.objects.select_for_update().get(
                    id=cuota_id,
                    venta=venta
                )
            except CuotaCredito.DoesNotExist:
                raise ValueError(f"Cuota con ID {cuota_id} no existe para esta venta")
            
            if cuota.estado == 'pagada':
                raise ValueError(f"La cuota {cuota.numero_cuota} ya está pagada")
            
            # Validar que el monto cubra la cuota
            if monto_pagado < cuota.monto_cuota:
                raise ValueError(
                    f"El monto debe ser al menos {cuota.monto_cuota} para pagar la cuota completa"
                )

        print(f"💵 Registrando pago de {monto_pagado} para Venta #{venta.pk}")

        pago = Pago.objects.create(
            venta=venta,
            cuota=cuota,
            monto_pagado=monto_pagado,
            metodo_pago=metodo_pago,
            referencia_pago=referencia_pago or ''
        )

        if cuota:
            cuota.estado = 'pagada'
            cuota.fecha_pago = timezone.now().date()
            cuota.save()
            print(f"   ✓ Cuota {cuota.numero_cuota} marcada como PAGADA")

        total_pagado_nuevo = total_pagado_anterior + monto_pagado

        # Actualizar estado de la venta
        if total_pagado_nuevo >= total_a_pagar:
            venta.estado = 'pagado'
            print(f"✅ Venta #{venta.pk} marcada como PAGADA")
        elif total_pagado_nuevo > 0:
            venta.estado = 'parcial'
            print(f"⚠️ Venta #{venta.pk} con pago PARCIAL "
                  f"({total_pagado_nuevo}/{total_a_pagar})")
        else:
            venta.estado = 'pendiente'

        venta.save()

        if not cuota and venta.tipo_venta == 'credito':
            PagoService._actualizar_cuotas_automaticamente(venta, total_pagado_nuevo)

        return pago

    @staticmethod
    def _actualizar_cuotas_automaticamente(venta, total_pagado):

        from apps.cuota.models import CuotaCredito

        cuotas = venta.cuotas.filter(estado__in=['pendiente', 'vencida']).order_by('numero_cuota')
        monto_restante = Decimal(str(total_pagado))

        for cuota in cuotas:
            if monto_restante >= cuota.monto_cuota:
                cuota.estado = 'pagada'
                cuota.fecha_pago = timezone.now().date()
                cuota.save()

                monto_restante -= cuota.monto_cuota
                print(f"   ✓ Cuota {cuota.numero_cuota} marcada como PAGADA automáticamente")
            else:
                break

    @staticmethod
    @transaction.atomic
    def registrar_pago_al_contado(venta_id, metodo_pago, referencia_pago=None):
        try:
            venta = Venta.objects.select_for_update().get(pk=venta_id)
        except Venta.DoesNotExist:
            raise ValueError(f"Venta con ID {venta_id} no existe")
        
        if venta.tipo_venta != 'contado':
            raise ValueError("Esta función solo es para ventas al contado")
        
        # Verificar si ya está pagada
        if venta.estado == 'pagado':
            raise ValueError("Esta venta ya está completamente pagada")
        
        # Registrar pago por el total
        print(f"💰 Registrando pago al contado de {venta.total} para Venta #{venta.pk}")
        
        pago = Pago.objects.create(
            venta=venta,
            monto_pagado=venta.total,
            metodo_pago=metodo_pago,
            referencia_pago=referencia_pago or 'Pago al contado'
        )
        
        # Marcar venta como pagada
        venta.estado = 'pagado'
        venta.save()
        
        print(f"✅ Venta al contado #{venta.pk} pagada completamente")
        
        return pago
