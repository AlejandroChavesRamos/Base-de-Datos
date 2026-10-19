from django.contrib import admin
from .models import Proveedor, Producto, Cliente, Pedido, DetallePedido

admin.site.site_title = 'EmpresaUN'
admin.site.index_title = 'Gestión de datos'


class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [DetalleInline]
    list_display = ('id_pedido', 'cliente', 'fecha_pedido')
    list_filter = ('fecha_pedido',)
    search_fields = ('cliente__nombre', 'cliente__apellidos', 'cliente__identificacion')
    date_hierarchy = 'fecha_pedido'


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'nombre', 'apellidos', 'fecha_nacimiento', 'usuario')
    search_fields = ('identificacion', 'nombre', 'apellidos')
    ordering = ('apellidos', 'nombre')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'precio_unitario', 'proveedor')
    list_filter = ('proveedor',)
    search_fields = ('codigo', 'nombre')


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nit', 'nombre', 'direccion')
    search_fields = ('nit', 'nombre')