# apps/orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/direccion/', views.checkout_direccion, name='checkout_direccion'),
    path('checkout/pago/', views.checkout_pago, name='checkout_pago'),
    path('checkout/resumen/', views.checkout_resumen, name='checkout_resumen'),
    path('checkout/confirmacion/', views.checkout_confirmacion, name='checkout_confirmacion'),
    path('historial/', views.historial_ordenes, name='historial_ordenes'),
    path('detalle/<str:numero_orden>/', views.detalle_orden, name='detalle_orden'),
    # Nuevas rutas para confirmar recepción y valorar productos
    path('confirmar-recepcion/<str:numero_orden>/', views.confirmar_recepcion, name='confirmar_recepcion'),
    path('valorar-productos/<str:numero_orden>/', views.valorar_productos, name='valorar_productos'),
]