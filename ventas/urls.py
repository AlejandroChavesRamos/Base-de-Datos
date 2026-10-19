from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),

    # Cliente
    path('catalogo/', views.catalogo, name='catalogo'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('nuevo-pedido/', views.nuevo_pedido, name='nuevo_pedido'),
    path('mis-pedidos/<int:pk>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),

    # Staff
    path('panel/', views.dashboard, name='dashboard'),
    path('panel/consulta/<int:n>/', views.consulta, name='consulta'),

    # CRUD del panel
    path('panel/clientes/', views.ClienteLista.as_view(), name='clientes'),
    path('panel/clientes/nuevo/', views.ClienteCrear.as_view(), name='cliente_nuevo'),
    path('panel/clientes/<int:pk>/editar/', views.ClienteEditar.as_view(), name='cliente_editar'),
    path('panel/clientes/<int:pk>/eliminar/', views.ClienteEliminar.as_view(), name='cliente_eliminar'),

    path('panel/productos/', views.ProductoLista.as_view(), name='productos'),
    path('panel/productos/nuevo/', views.ProductoCrear.as_view(), name='producto_nuevo'),
    path('panel/productos/<str:pk>/editar/', views.ProductoEditar.as_view(), name='producto_editar'),
    path('panel/productos/<str:pk>/eliminar/', views.ProductoEliminar.as_view(), name='producto_eliminar'),

    path('panel/proveedores/', views.ProveedorLista.as_view(), name='proveedores'),
    path('panel/proveedores/nuevo/', views.ProveedorCrear.as_view(), name='proveedor_nuevo'),
    path('panel/proveedores/<str:pk>/editar/', views.ProveedorEditar.as_view(), name='proveedor_editar'),
    path('panel/proveedores/<str:pk>/eliminar/', views.ProveedorEliminar.as_view(), name='proveedor_eliminar'),

    path('panel/pedidos/', views.PedidoLista.as_view(), name='pedidos'),
    path('panel/pedidos/<int:pk>/eliminar/', views.PedidoEliminar.as_view(), name='pedido_eliminar'),
]