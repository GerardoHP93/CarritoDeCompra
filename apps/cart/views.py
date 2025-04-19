import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.products.models import Producto
from .models import Carrito, ItemCarrito

# Configurar el logger
logger = logging.getLogger('apps.cart')

@login_required
def add_to_cart(request, product_id):
    """
    Vista para agregar un producto al carrito.
    """
    if request.method == 'POST':
        product = get_object_or_404(Producto, id=product_id, activo=True)
        quantity = int(request.POST.get('quantity', 1))
        
        # Por ahora, solo registrar la acción
        logger.debug(f'Intento de agregar al carrito: {product.nombre}, cantidad: {quantity}')
        messages.success(request, f'Se agregó {product.nombre} al carrito.')
        
        # Redirigir a la página de detalles del producto
        return redirect('products:product_detail', slug=product.slug)
    
    # Si no es POST, redirigir a la lista de productos
    return redirect('products:product_list')

@login_required
def remove_from_cart(request, product_id):
    """
    Vista para eliminar un producto del carrito.
    """
    logger.debug(f'Intento de eliminar del carrito: producto_id={product_id}')
    messages.success(request, 'Producto eliminado del carrito.')
    return redirect('cart:cart_detail')

@login_required
def update_cart(request, product_id):
    """
    Vista para actualizar la cantidad de un producto en el carrito.
    """
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        logger.debug(f'Intento de actualizar carrito: producto_id={product_id}, cantidad={quantity}')
        messages.success(request, 'Carrito actualizado.')
    
    return redirect('cart:cart_detail')

@login_required
def cart_detail(request):
    """
    Vista para mostrar el contenido del carrito.
    """
    logger.debug(f'Vista del carrito para usuario: {request.user.username}')
    return render(request, 'cart/cart_detail.html')