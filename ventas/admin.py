from django.contrib import admin
from .models import Proveedor, Producto, Cliente, Pedido, DetallePedido


class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [DetalleInline]
    list_display = ('id_pedido', 'cliente', 'fecha_pedido')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'nombre', 'apellidos', 'fecha_nacimiento')
    search_fields = ('identificacion', 'nombre', 'apellidos')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'precio_unitario', 'proveedor')


admin.site.register(Proveedor)