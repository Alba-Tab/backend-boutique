from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Pago
from apps.venta.models import Venta


class PagoService:
    """
    Servicio para manejar registros de pagos y actualizar estados
    """

    @staticmethod
    @transaction.atomic
    def registrar_pago(venta_id, monto_pagado, metodo_pago, referencia_pago=None):
        """
        Registra un pago y actualiza el estado de la venta

        Args:
            venta_id (int): ID de la venta
            monto_pagado (Decimal): Monto del pago
            metodo_pago (str): Método de pago ('efectivo', 'tarjeta', 'qr')
            referencia_pago (str): Referencia opcional del pago

        Returns:
            Pago: Instancia del pago creado

        Raises:
            ValueError: Si hay errores de validación
        """

        # ========================================
        # 1. OBTENER VENTA
        # ========================================
        try:
            venta = Venta.objects.select_for_update().get(id=venta_id)
        except Venta.DoesNotExist:
            raise ValueError(f"Venta con ID {venta_id} no existe")

        # ========================================
        # 2. VALIDAR MONTO
        # ========================================
        monto_pagado = Decimal(str(monto_pagado))

        if monto_pagado <= 0:
            raise ValueError("El monto debe ser mayor a 0")

        # Calcular total a pagar (con interés si es crédito)
        total_a_pagar = (
            venta.total_con_interes
            if venta.tipo_pago == 'credito'
            else venta.total
        )

        # Calcular total ya pagado
        total_pagado_anterior = sum(
            p.monto_pagado for p in venta.pagos.all()
        )

        # Validar que no se pague más del total
        if (total_pagado_anterior + monto_pagado) > total_a_pagar:
            raise ValueError(
                f"El pago excede el total. "
                f"Total: {total_a_pagar}, "
                f"Ya pagado: {total_pagado_anterior}, "
                f"Falta: {total_a_pagar - total_pagado_anterior}"
            )

        # ========================================
        # 3. CREAR EL PAGO
        # ========================================
        print(f"💵 Registrando pago de {monto_pagado} para Venta #{venta.id}")

        pago = Pago.objects.create(
            venta=venta,
            monto_pagado=monto_pagado,
            metodo_pago=metodo_pago,
            referencia_pago=referencia_pago
        )

        # ========================================
        # 4. ACTUALIZAR ESTADO DE LA VENTA
        # ========================================
        total_pagado_nuevo = total_pagado_anterior + monto_pagado

        if total_pagado_nuevo >= total_a_pagar:
            venta.estado_pago = 'pagado'
            print(f"✅ Venta #{venta.id} marcada como PAGADA")
        elif total_pagado_nuevo > 0:
            venta.estado_pago = 'parcial'
            print(f"⚠️ Venta #{venta.id} con pago PARCIAL "
                  f"({total_pagado_nuevo}/{total_a_pagar})")
        else:
            venta.estado_pago = 'pendiente'

        venta.save()

        # ========================================
        # 5. MARCAR CUOTAS COMO PAGADAS (si es crédito)
        # ========================================
        if venta.tipo_pago == 'credito':
            PagoService._actualizar_cuotas(venta, total_pagado_nuevo)

        return pago


    @staticmethod
    def _actualizar_cuotas(venta, total_pagado):
        """
        Marca cuotas como pagadas según el monto acumulado

        Args:
            venta (Venta): Instancia de la venta
            total_pagado (Decimal): Total pagado hasta ahora
        """
        from apps.cuota.models import CuotaCredito

        cuotas = venta.cuotas.filter(estado='pendiente').order_by('numero_cuota')
        monto_restante = total_pagado

        for cuota in cuotas:
            if monto_restante >= cuota.monto_cuota:
                cuota.estado = 'pagada'
                cuota.fecha_pago = timezone.now().date()
                cuota.save()

                monto_restante -= cuota.monto_cuota
                print(f"   ✓ Cuota {cuota.numero_cuota} marcada como PAGADA")
            else:
                break
