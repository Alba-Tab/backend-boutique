from django.contrib import admin
from .models import Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ['sub_total', 'nombre_producto', 'talla']
    fields = ['variante_producto', 'cantidad', 'precio_unitario', 'sub_total', 'nombre_producto', 'talla']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_cliente_info',
        'get_vendedor_info',
        'fecha',
        'total',
        'tipo_venta',
        'estado',
    ]
    list_filter = ['tipo_venta', 'estado', 'fecha', 'vendedor']
    search_fields = ['cliente__email', 'nombre_cliente', 'vendedor__username', 'id']
    inlines = [DetalleVentaInline]
    readonly_fields = ['fecha', 'total', 'total_con_interes', 'cuota_mensual', 'nombre_vendedor']
    
    def get_cliente_info(self, obj):
        """Muestra nombre o email del cliente"""
        if obj.nombre_cliente:
            return obj.nombre_cliente
        return obj.cliente.email if obj.cliente else "Sin cliente"
    get_cliente_info.short_description = 'Cliente'
    
    def get_vendedor_info(self, obj):
        """Muestra nombre del vendedor"""
        return obj.nombre_vendedor or obj.vendedor.username
    get_vendedor_info.short_description = 'Vendedor'


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'venta',
        'nombre_producto',
        'talla',
        'cantidad',
        'precio_unitario',
        'sub_total',
    ]
    list_filter = ['venta__fecha']
    search_fields = ['nombre_producto', 'venta__id']
    readonly_fields = ['sub_total', 'nombre_producto', 'talla']

