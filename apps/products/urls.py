# apps/products/urls.py
from django.urls import path
from . import views
from . import inventory_views  # Asegúrate de importar las vistas de inventario

app_name = 'products'

urlpatterns = [
    # URLs normales de productos
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('search/', views.product_search, name='product_search'),
    
    # URLs de gestión de inventario (ANTES de la URL con slug)
    path('inventario/', inventory_views.dashboard_inventario, name='dashboard_inventario'),
    path('inventario/pedidos/', inventory_views.lista_pedidos_proveedor, name='lista_pedidos_proveedor'),
    path('inventario/pedidos/crear/', inventory_views.crear_pedido_proveedor, name='crear_pedido_proveedor'),
    path('inventario/pedidos/<str:numero_pedido>/', inventory_views.detalle_pedido_proveedor, name='detalle_pedido_proveedor'),
    path('inventario/pedidos/<str:numero_pedido>/editar/', inventory_views.editar_pedido_proveedor, name='editar_pedido_proveedor'),
    path('inventario/pedidos/<str:numero_pedido>/cancelar/', inventory_views.cancelar_pedido_proveedor, name='cancelar_pedido_proveedor'),
    path('inventario/pedidos/<str:numero_pedido>/pagar/', inventory_views.pagar_pedido_proveedor, name='pagar_pedido_proveedor'),
    path('inventario/pedidos/<str:numero_pedido>/recibir/', inventory_views.recibir_pedido_proveedor, name='recibir_pedido_proveedor'),
    path('inventario/api/productos-proveedor/<int:proveedor_id>/', inventory_views.obtener_productos_proveedor, name='obtener_productos_proveedor'),
    
    # URL con slug para detalle de producto (DEBE IR AL FINAL)
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]