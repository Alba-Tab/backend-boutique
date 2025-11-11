# apps/venta/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.pago.services import PagoService
from apps.pago.serializers import PagoSerializer, PagoAlContadoSerializer
from .models import Venta
from .serializers import (
    VentaListSerializer,
    VentaDetailSerializer,
    CrearVentaSerializer,
    DetalleVentaSerializer
)
from .services import VentaService

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all().order_by('-fecha')
    # permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VentaDetailSerializer  # Con detalles
        return VentaListSerializer  # Sin detalles

    # def get_queryset(self):
    #     user = self.request.user
    #     if user.is_staff:
    #         return Venta.objects.all().select_related('cliente')
    #     return Venta.objects.filter(cliente=user).select_related('cliente')

    @action(detail=False, methods=['get'], url_path='mis-pedidos', permission_classes=[IsAuthenticated])
    def mis_pedidos(self, request):
        """
        Endpoint para que clientes vean sus pedidos
        GET /api/ventas/mis-pedidos/
        """
        # Debug: verificar autenticación
        print(f"Usuario: {request.user}")
        print(f"Es autenticado: {request.user.is_authenticated}")
        print(f"Rol: {getattr(request.user, 'rol', 'No tiene rol')}")
        print(f"ID Usuario: {request.user.id if request.user.is_authenticated else 'N/A'}")

        # if request.user.rol != 'cliente':
        #     return Response(
        #         {'error': 'Solo clientes pueden acceder a este endpoint'},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        # Debug: ver TODAS las ventas del usuario
        todas_ventas_usuario = Venta.objects.filter(cliente=request.user)
        print(f"Total ventas del usuario (cualquier origen): {todas_ventas_usuario.count()}")

        # Debug: ver qué orígenes tienen
        for v in todas_ventas_usuario:
            print(f"  Venta ID {v.id}: origen='{v.origen}', cliente={v.cliente_id}")

        ventas = Venta.objects.filter(
            cliente=request.user,
            origen='ecommerce'
        ).select_related('cliente').order_by('-fecha')

        print(f"Ventas con origen='ecommerce': {ventas.count()}")

        # Filtros opcionales
        estado = request.query_params.get('estado')
        if estado:
            ventas = ventas.filter(estado=estado)

        tipo_venta = request.query_params.get('tipo_venta')
        if tipo_venta:
            ventas = ventas.filter(tipo_venta=tipo_venta)

        serializer = VentaListSerializer(ventas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def crear(self, request):
        serializer = CrearVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Obtener vendedor_id del JSON (si viene)
        vendedor_id = serializer.validated_data.get('vendedor')

        # Si NO viene en JSON pero el usuario logueado es vendedor, usar automático
        if not vendedor_id and request.user.is_authenticated and request.user.rol == 'vendedor':
            vendedor_id = request.user.id
            print(f"🔐 Vendedor detectado automáticamente: {request.user.username} (ID: {vendedor_id})")

        # Obtener cliente_id del JSON (si viene)
        cliente_id = serializer.validated_data.get('cliente')

        # Si NO viene en JSON pero el usuario logueado es cliente, usar automático
        if not cliente_id and request.user.is_authenticated and request.user.rol == 'cliente':
            cliente_id = request.user.id
            print(f"🔐 Cliente detectado automáticamente: {request.user.username} (ID: {cliente_id})")

        try:
            venta = VentaService.crear_venta(
                items=serializer.validated_data['items'],
                tipo_venta=serializer.validated_data['tipo_venta'],
                origen=serializer.validated_data.get('origen', 'tienda'),
                vendedor_id=vendedor_id,
                cliente_id=cliente_id,
                interes=serializer.validated_data.get('interes'),
                plazo_meses=serializer.validated_data.get('plazo_meses'),
                correo_cliente=serializer.validated_data.get('correo_cliente'),
                direccion_cliente=serializer.validated_data.get('direccion_cliente'),
                nombre_cliente=serializer.validated_data.get('nombre_cliente'),
                telefono_cliente=serializer.validated_data.get('telefono_cliente'),
                numero_cliente=serializer.validated_data.get('numero_cliente'),
                estado=serializer.validated_data.get('estado', 'pendiente')
            )

            response_serializer = VentaDetailSerializer(venta)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        """GET /api/ventas/{id}/detalles/"""
        venta = self.get_object()
        detalles = venta.detalles.all()
        serializer = DetalleVentaSerializer(detalles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pagar_al_contado(self, request, pk=None):
        venta = self.get_object()

        if venta.tipo_venta != 'contado':
            return Response(
                {'error': 'Esta venta no es al contado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PagoAlContadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            pago = PagoService.registrar_pago_al_contado(
                venta_id=venta.pk,
                metodo_pago=serializer.validated_data['metodo_pago'],
                referencia_pago=serializer.validated_data.get('referencia_pago')
            )

            pago_serializer = PagoSerializer(pago)
            venta_serializer = VentaDetailSerializer(venta)

            return Response({
                'message': 'Venta pagada completamente',
                'pago': pago_serializer.data,
                'venta': venta_serializer.data
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def agregar_detalle(self, request, pk=None):
        """POST /api/ventas/{id}/agregar_detalle/
        """
        venta = self.get_object()

        serializer = DetalleVentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        detalle = serializer.save(venta=venta)

        return Response(
            DetalleVentaSerializer(detalle).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'])
    def actualizar_detalle(self, request, pk=None):
        """PATCH /api/ventas/{id}/actualizar_detalle/?detalle_id=X
        """
        venta = self.get_object()
        detalle_id = request.query_params.get('detalle_id')

        if not detalle_id:
            return Response(
                {'error': 'detalle_id es requerido como query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            detalle = venta.detalles.get(id=detalle_id)

            serializer = DetalleVentaSerializer(detalle, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # Recalcular total
            venta.calcular_total()

            return Response(DetalleVentaSerializer(detalle).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def eliminar_detalle(self, request, pk=None):
        """DELETE /api/ventas/{id}/eliminar_detalle/?detalle_id=X
        Elimina un detalle específico de la venta
        """
        venta = self.get_object()
        detalle_id = request.query_params.get('detalle_id')

        if not detalle_id:
            return Response(
                {'error': 'detalle_id es requerido como query parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            detalle = venta.detalles.get(id=detalle_id)
            detalle.delete()

            # Recalcular total
            venta.calcular_total()

            return Response(
                {'message': 'Detalle eliminado correctamente'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    # @action(detail=True, methods=['get'])
    # def detalles(self, request, pk=None):
    #     """GET /api/ventas/{id}/detalles/"""
    #     venta = self.get_object()

    #     detalles = venta.detalles.all()
    #     serializer = VentaDetailSerializer(detalles, many=True)

    #     return Response(serializer.data)
