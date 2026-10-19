from django.conf import settings
from django.db import models

class Proveedor(models.Model):
    nit = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=150)

    class Meta:
        db_table = 'proveedor'
        verbose_name_plural = 'proveedores'

    def __str__(self):
        return f"{self.nit} - {self.nombre}"


class Producto(models.Model):
    codigo = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=100)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column='nit_proveedor',
        related_name='productos',
    )

    class Meta:
        db_table = 'producto'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name='ck_precio_no_negativo',
            ),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_usuario',
        related_name='cliente',
    )
    identificacion = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=60)
    apellidos = models.CharField(max_length=60)
    direccion = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField()

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        db_column='id_cliente',
        related_name='pedidos',
    )
    fecha_pedido = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'pedido'

    def __str__(self):
        return f"Pedido {self.id_pedido} - {self.cliente}"


class DetallePedido(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        db_column='id_pedido',
        related_name='detalles',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        db_column='codigo_producto',
        related_name='detalles',
    )
    cantidad = models.PositiveIntegerField()
    precio_compra = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True
    )

    class Meta:
        db_table = 'detalle_pedido'
        constraints = [
            models.UniqueConstraint(
                fields=['pedido', 'producto'], name='uq_pedido_producto'
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='ck_cantidad_positiva',
            ),
        ]

    def save(self, *args, **kwargs):
        # Si no se escribe precio, se copia el precio actual del producto
        if self.precio_compra is None:
            self.precio_compra = self.producto.precio_unitario
        super().save(*args, **kwargs)