from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm, ProductoForm, ProveedorForm, RegistroForm
from .models import Cliente, DetallePedido, Pedido, Producto, Proveedor

from django.contrib.auth import login

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView



def registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save()
        login(request, cliente.usuario)
        messages.success(request, f'¡Bienvenido, {cliente.nombre}! Tu cuenta fue creada.')
        return redirect('inicio')

    return render(request, 'registration/registro.html', {'form': form})


# ---------- Control de acceso ----------
def staff_required(view):
    """Solo usuarios con is_staff. Los demás reciben 403."""
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def cliente_actual(request):
    return getattr(request.user, 'cliente', None)


@login_required
def inicio(request):
    if request.user.is_staff:
        return redirect('dashboard')
    return redirect('catalogo')


def registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save()
        login(request, cliente.usuario)
        messages.success(request, f'¡Bienvenido, {cliente.nombre}! Tu cuenta fue creada.')
        return redirect('inicio')

    return render(request, 'registration/registro.html', {'form': form})


# ---------- Cliente ----------
@login_required
def catalogo(request):
    q = request.GET.get('q', '').strip()
    productos = Producto.objects.select_related('proveedor').order_by('nombre')
    if q:
        productos = productos.filter(nombre__icontains=q)
    return render(request, 'ventas/catalogo.html', {'productos': productos, 'q': q})


@login_required
def mis_pedidos(request):
    cliente = cliente_actual(request)
    if cliente is None:
        messages.error(request, 'Tu usuario aún no está asociado a un cliente. Contacta al administrador.')
        return render(request, 'ventas/mis_pedidos.html', {'pedidos': []})

    total = ExpressionWrapper(
        F('detalles__cantidad') * F('detalles__precio_compra'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    pedidos = (Pedido.objects.filter(cliente=cliente)
               .prefetch_related('detalles__producto')
               .annotate(total=Sum(total))
               .order_by('-fecha_pedido', '-id_pedido'))
    return render(request, 'ventas/mis_pedidos.html', {'pedidos': pedidos})


@login_required
def cancelar_pedido(request, pk):
    if request.method != 'POST':
        return redirect('mis_pedidos')

    cliente = cliente_actual(request)
    if cliente is None:
        messages.error(request, 'Tu usuario aún no está asociado a un cliente.')
        return redirect('mis_pedidos')

    pedido = get_object_or_404(Pedido, pk=pk, cliente=cliente)
    numero = pedido.id_pedido
    pedido.delete()
    messages.success(request, f'Pedido #{numero} cancelado.', extra_tags='eliminado cancelado')
    return redirect('mis_pedidos')


@login_required
def nuevo_pedido(request):
    cliente = cliente_actual(request)
    if cliente is None:
        messages.error(request, 'Tu usuario aún no está asociado a un cliente.')
        return redirect('catalogo')

    productos = Producto.objects.select_related('proveedor').order_by('nombre')

    if request.method == 'POST':
        items = []
        for p in productos:
            try:
                cantidad = int(request.POST.get(f'cant_{p.codigo}', 0))
            except ValueError:
                cantidad = 0
            if cantidad > 0:
                items.append((p, cantidad))

        if not items:
            messages.error(request, 'Elige al menos un producto con cantidad mayor a 0.')
        else:
            with transaction.atomic():
                pedido = Pedido.objects.create(cliente=cliente)
                DetallePedido.objects.bulk_create([
                    DetallePedido(pedido=pedido, producto=p, cantidad=c,
                                  precio_compra=p.precio_unitario)
                    for p, c in items
                ])
            messages.success(request, f'Pedido #{pedido.id_pedido} registrado.', extra_tags='pedido')
            return redirect('mis_pedidos')

    return render(request, 'ventas/nuevo_pedido.html', {'productos': productos})


# ---------- Staff ----------
@staff_required
def dashboard(request):
    contexto = {
        'n_clientes': Cliente.objects.count(),
        'n_productos': Producto.objects.count(),
        'n_proveedores': Proveedor.objects.count(),
        'n_pedidos': Pedido.objects.count(),
        'ultimos': Pedido.objects.select_related('cliente').order_by('-id_pedido')[:5],
    }
    return render(request, 'ventas/dashboard.html', contexto)


CONSULTAS = {
    1: ('Clientes y cantidad de pedidos', """
        SELECT c.identificacion,
               CONCAT(c.nombre, ' ', c.apellidos) AS cliente,
               COUNT(p.id_pedido) AS total_pedidos
        FROM cliente c
        LEFT JOIN pedido p ON p.id_cliente = c.id_cliente
        GROUP BY c.id_cliente, c.identificacion, c.nombre, c.apellidos
        ORDER BY total_pedidos DESC
    """),
    2: ('Clientes sin pedidos', """
        SELECT c.identificacion,
               CONCAT(c.nombre, ' ', c.apellidos) AS cliente,
               c.direccion
        FROM cliente c
        LEFT JOIN pedido p ON p.id_cliente = c.id_cliente
        WHERE p.id_pedido IS NULL
    """),
    3: ('Detalle de compras por cliente', """
        SELECT CONCAT(c.nombre, ' ', c.apellidos) AS cliente,
               pr.nombre AS producto,
               d.cantidad,
               d.precio_compra,
               pv.nombre AS proveedor
        FROM detalle_pedido d
        JOIN pedido p     ON p.id_pedido = d.id_pedido
        JOIN cliente c    ON c.id_cliente = p.id_cliente
        JOIN producto pr  ON pr.codigo = d.codigo_producto
        JOIN proveedor pv ON pv.nit = pr.nit_proveedor
        ORDER BY cliente, producto
    """),
    4: ('Proveedores y sus productos', """
        SELECT pv.nit, pv.nombre AS proveedor,
               pr.codigo, pr.nombre AS producto
        FROM proveedor pv
        LEFT JOIN producto pr ON pr.nit_proveedor = pv.nit
        ORDER BY pv.nombre, pr.nombre
    """),
}


@staff_required
def consulta(request, n):
    if n not in CONSULTAS:
        raise Http404
    titulo, sql = CONSULTAS[n]
    with connection.cursor() as cur:
        cur.execute(sql)
        columnas = [c[0].replace('_', ' ') for c in cur.description]
        filas = cur.fetchall()
    return render(request, 'ventas/consulta.html', {
        'n': n, 'titulo': titulo, 'sql': sql.strip(),
        'columnas': columnas, 'filas': filas,
    })

class StaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied          # logueado pero sin permiso: 403
        return super().handle_no_permission()   # sin login: va al login


class BaseLista(StaffMixin, ListView):
    template_name = 'crud/lista.html'
    paginate_by = 10
    titulo = ''
    prefijo = ''              # 'cliente' -> usa las rutas cliente_nuevo, cliente_editar...
    columnas = []             # [('Título visible', 'atributo_del_modelo'), ...]
    search_fields = []
    con_nuevo = True
    con_editar = True

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        if q:
            cond = Q()
            for campo in self.search_fields:
                cond |= Q(**{f'{campo}__icontains': q})
            qs = qs.filter(cond)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = self.prefijo
        ctx['titulo'] = self.titulo
        ctx['q'] = self.request.GET.get('q', '')
        ctx['columnas'] = [c[0] for c in self.columnas]
        ctx['url_nuevo'] = reverse(f'{p}_nuevo') if self.con_nuevo else None
        ctx['filas'] = [{
            'valores': [getattr(o, attr) for _, attr in self.columnas],
            'editar': reverse(f'{p}_editar', args=[o.pk]) if self.con_editar else None,
            'eliminar': reverse(f'{p}_eliminar', args=[o.pk]),
        } for o in ctx['object_list']]
        return ctx


class BaseForm(StaffMixin):
    template_name = 'crud/form.html'
    titulo = ''
    lista = ''                # nombre de la ruta de la lista
    mensaje = ''

    def get_success_url(self):
        return reverse(self.lista)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = self.titulo
        ctx['url_volver'] = reverse(self.lista)
        return ctx

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje)
        return respuesta


class BaseEliminar(StaffMixin, DeleteView):
    http_method_names = ['post']     # borrar solo se permite por POST
    lista = ''
    nombre = 'Registro'              # se muestra en el aviso: "Cliente eliminado."
    motivo = ''                      # por qué puede estar protegido

    def form_valid(self, form):
        try:
            self.object.delete()
            messages.success(self.request, f'{self.nombre} eliminado.', extra_tags='eliminado')
        except ProtectedError:
            messages.error(self.request, f'No se puede eliminar: {self.motivo}.')
        return redirect(self.lista)


# ---------- Clientes ----------
class ClienteLista(BaseLista):
    model = Cliente
    titulo, prefijo = 'Clientes', 'cliente'
    ordering = ['apellidos', 'nombre']
    search_fields = ['identificacion', 'nombre', 'apellidos']
    columnas = [('Identificación', 'identificacion'), ('Nombre', 'nombre'),
                ('Apellidos', 'apellidos'), ('Nacimiento', 'fecha_nacimiento')]

class ClienteCrear(BaseForm, CreateView):
    model, form_class = Cliente, ClienteForm
    titulo, lista, mensaje = 'Nuevo cliente', 'clientes', 'Cliente creado.'

class ClienteEditar(BaseForm, UpdateView):
    model, form_class = Cliente, ClienteForm
    titulo, lista, mensaje = 'Editar cliente', 'clientes', 'Cliente actualizado.'

class ClienteEliminar(BaseEliminar):
    model, lista = Cliente, 'clientes'
    nombre = 'Cliente'
    motivo = 'el cliente tiene pedidos registrados'


# ---------- Productos ----------
class ProductoLista(BaseLista):
    model = Producto
    queryset = Producto.objects.select_related('proveedor')
    titulo, prefijo = 'Productos', 'producto'
    ordering = ['nombre']
    search_fields = ['codigo', 'nombre', 'proveedor__nombre']
    columnas = [('Código', 'codigo'), ('Nombre', 'nombre'),
                ('Precio', 'precio_unitario'), ('Proveedor', 'proveedor')]

class ProductoCrear(BaseForm, CreateView):
    model, form_class = Producto, ProductoForm
    titulo, lista, mensaje = 'Nuevo producto', 'productos', 'Producto creado.'

class ProductoEditar(BaseForm, UpdateView):
    model, form_class = Producto, ProductoForm
    titulo, lista, mensaje = 'Editar producto', 'productos', 'Producto actualizado.'

class ProductoEliminar(BaseEliminar):
    model, lista = Producto, 'productos'
    nombre = 'Producto'
    motivo = 'el producto aparece en pedidos'


# ---------- Proveedores ----------
class ProveedorLista(BaseLista):
    model = Proveedor
    titulo, prefijo = 'Proveedores', 'proveedor'
    ordering = ['nombre']
    search_fields = ['nit', 'nombre', 'direccion']
    columnas = [('NIT', 'nit'), ('Nombre', 'nombre'), ('Dirección', 'direccion')]

class ProveedorCrear(BaseForm, CreateView):
    model, form_class = Proveedor, ProveedorForm
    titulo, lista, mensaje = 'Nuevo proveedor', 'proveedores', 'Proveedor creado.'

class ProveedorEditar(BaseForm, UpdateView):
    model, form_class = Proveedor, ProveedorForm
    titulo, lista, mensaje = 'Editar proveedor', 'proveedores', 'Proveedor actualizado.'

class ProveedorEliminar(BaseEliminar):
    model, lista = Proveedor, 'proveedores'
    nombre = 'Proveedor'
    motivo = 'el proveedor tiene productos asociados'


# ---------- Pedidos (lista y eliminar; los crean los clientes) ----------
class PedidoLista(BaseLista):
    model = Pedido
    queryset = Pedido.objects.select_related('cliente').annotate(
        total=Sum(ExpressionWrapper(
            F('detalles__cantidad') * F('detalles__precio_compra'),
            output_field=DecimalField(max_digits=12, decimal_places=2))))
    titulo, prefijo = 'Pedidos', 'pedido'
    ordering = ['-id_pedido']
    con_nuevo = False
    con_editar = False
    search_fields = ['cliente__nombre', 'cliente__apellidos', 'cliente__identificacion']
    columnas = [('N.º', 'id_pedido'), ('Cliente', 'cliente'),
                ('Fecha', 'fecha_pedido'), ('Total', 'total')]

class PedidoEliminar(BaseEliminar):
    model, lista = Pedido, 'pedidos'
    nombre = 'Pedido'
    motivo = 'no fue posible borrar el pedido'