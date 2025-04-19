from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-ajax/<int:product_id>/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),
    path('update-ajax/<int:product_id>/', views.update_cart_ajax, name='update_cart_ajax'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.cart_detail, name='cart_detail'),
]