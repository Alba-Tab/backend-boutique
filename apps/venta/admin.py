from django.contrib import admin
from .models import Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ['subtotal', 'producto_nombre', 'talla', 'color']
    fields = ['variante', 'cantidad', 'precio_unitario', 'subtotal', 'producto_nombre', 'talla', 'color']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_cliente_info',
        'fecha',
        'total',
        'tipo_pago',
        'estado_pago',
    ]
    list_filter = ['tipo_pago', 'estado_pago', 'fecha']
    search_fields = ['cliente__email', 'id']
    inlines = [DetalleVentaInline]
    readonly_fields = ['fecha', 'total', 'total_con_interes', 'cuota_mensual']
    
    def get_cliente_info(self, obj):
        """Muestra email del cliente o 'Sin cliente'"""
        return obj.cliente.email if obj.cliente else "Sin cliente"
    get_cliente_info.short_description = 'Cliente'


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'venta',
        'producto_nombre',
        'talla',
        'color',
        'cantidad',
        'precio_unitario',
        'subtotal',
    ]
    list_filter = ['venta__fecha']
    search_fields = ['producto_nombre', 'venta__id']
    readonly_fields = ['subtotal', 'producto_nombre', 'talla', 'color']

