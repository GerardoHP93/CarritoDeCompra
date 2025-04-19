import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
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

        # Verificar stock
        if quantity > product.stock:
            messages.error(
                request, f'Lo sentimos, solo hay {product.stock} unidades disponibles de {product.nombre}.')
            return redirect('products:product_detail', slug=product.slug)

        # Obtener o crear el carrito del usuario
        cart, created = Carrito.objects.get_or_create(usuario=request.user)

        # Verificar si el producto ya está en el carrito
        try:
            cart_item = cart.items.get(producto=product)
            # Si ya existe, actualizar la cantidad
            if cart_item.cantidad + quantity > product.stock:
                messages.warning(
                    request, f'No puedes agregar más unidades. Stock disponible: {product.stock}')
            else:
                cart_item.cantidad = F('cantidad') + quantity
                cart_item.save()
                cart_item.refresh_from_db()  # Actualizar después de usar F()
                messages.success(
                    request, f'Se actualizó la cantidad de {product.nombre} en tu carrito a {cart_item.cantidad}.')
        except ItemCarrito.DoesNotExist:
            # Si no existe, crear nuevo item
            cart_item = ItemCarrito(
                carrito=cart, producto=product, cantidad=quantity)
            cart_item.save()
            messages.success(
                request, f'Se agregó {product.nombre} a tu carrito.')

        logger.debug(
            f'Producto agregado/actualizado en carrito: {product.nombre}, cantidad: {quantity}')

        # Verificar si es una solicitud AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'cart_count': cart.cantidad_productos,
                'message': f'Se agregó {product.nombre} a tu carrito.'
            })

        # Redirigir a la página de detalles del producto
        return redirect('products:product_detail', slug=product.slug)

    # Si no es POST, redirigir a la lista de productos
    return redirect('products:product_list')


@login_required
def remove_from_cart(request, product_id):
    """
    Vista para eliminar un producto del carrito.
    """
    if request.method == 'POST':
        product = get_object_or_404(Producto, id=product_id)

        try:
            cart = Carrito.objects.get(usuario=request.user)
            cart_item = cart.items.get(producto=product)

            product_name = product.nombre
            cart_item.delete()

            logger.debug(f'Producto eliminado del carrito: {product_name}')
            messages.success(request, f'{product_name} eliminado del carrito.')

            # Verificar si es una solicitud AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'cart_count': cart.cantidad_productos,
                    'cart_total': cart.total,
                    'message': f'{product_name} eliminado del carrito.'
                })

        except (Carrito.DoesNotExist, ItemCarrito.DoesNotExist) as e:
            logger.error(f'Error al eliminar producto: {str(e)}')
            messages.error(request, 'Producto no encontrado en el carrito.')

    return redirect('cart:cart_detail')


@login_required
def update_cart(request, product_id):
    """
    Vista para actualizar la cantidad de un producto en el carrito.
    """
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1

        try:
            product = get_object_or_404(Producto, id=product_id)
            cart = Carrito.objects.get(usuario=request.user)
            cart_item = cart.items.get(producto=product)

            # Verificar stock disponible
            if quantity > product.stock:
                messages.warning(
                    request, f'Solo hay {product.stock} unidades disponibles.')
                quantity = product.stock

            # Actualizar cantidad
            cart_item.cantidad = quantity
            cart_item.save()

            logger.debug(
                f'Carrito actualizado: {product.nombre}, cantidad={quantity}')

            # Ya no mostramos mensaje de actualización
            # messages.success(request, 'Carrito actualizado.')

            # Verificar si es una solicitud AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'item_subtotal': cart_item.subtotal,
                    'cart_total': cart.total,
                    'cart_count': cart.cantidad_productos
                })

        except (Carrito.DoesNotExist, ItemCarrito.DoesNotExist, Producto.DoesNotExist) as e:
            logger.error(f'Error al actualizar carrito: {str(e)}')
            messages.error(request, 'Error al actualizar el carrito.')

    return redirect('cart:cart_detail')


@login_required
def cart_detail(request):
    """
    Vista para mostrar el contenido del carrito.
    """
    try:
        cart, created = Carrito.objects.get_or_create(usuario=request.user)
        cart_items = cart.items.all().select_related('producto')
    except Exception as e:
        logger.error(f'Error al acceder al carrito: {str(e)}')
        cart_items = []
        cart = None

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'active_step': 'items',  # Para indicar el paso activo en el proceso de compra
    }

    logger.debug(f'Vista del carrito para usuario: {request.user.username}')
    return render(request, 'cart/cart_detail.html', context)


@login_required
def clear_cart(request):
    """
    Vista para vaciar completamente el carrito.
    """
    if request.method == 'POST':
        try:
            cart = Carrito.objects.get(usuario=request.user)
            cart.items.all().delete()
            messages.success(request, 'El carrito ha sido vaciado.')
            logger.debug(
                f'Carrito vaciado para usuario: {request.user.username}')
        except Carrito.DoesNotExist:
            logger.error(f'Error al vaciar carrito: Carrito no existe')

    return redirect('cart:cart_detail')


@login_required
def remove_from_cart_ajax(request, product_id):
    """
    Vista AJAX para eliminar un producto del carrito sin redirección.
    """
    if request.method == 'POST':
        product = get_object_or_404(Producto, id=product_id)

        try:
            cart = Carrito.objects.get(usuario=request.user)
            cart_item = cart.items.get(producto=product)
            cart_item.delete()

            # Devolver respuesta JSON
            return JsonResponse({
                'status': 'success',
                'cart_count': cart.cantidad_productos,
                'cart_total': float(cart.total),
                'message': f'{product.nombre} eliminado del carrito.'
            })

        except (Carrito.DoesNotExist, ItemCarrito.DoesNotExist) as e:
            logger.error(f'Error al eliminar producto: {str(e)}')
            return JsonResponse({
                'status': 'error',
                'message': 'Producto no encontrado en el carrito.'
            }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)


@login_required
def update_cart_ajax(request, product_id):
    """
    Vista AJAX para actualizar la cantidad de un producto en el carrito sin redirección.
    """
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            quantity = 1

        try:
            product = get_object_or_404(Producto, id=product_id)
            cart = Carrito.objects.get(usuario=request.user)
            cart_item = cart.items.get(producto=product)

            # Verificar stock disponible
            if quantity > product.stock:
                return JsonResponse({
                    'status': 'warning',
                    'message': f'Solo hay {product.stock} unidades disponibles.'
                })

            # Actualizar cantidad
            cart_item.cantidad = quantity
            cart_item.save()

            # Recalcular valores
            return JsonResponse({
                'status': 'success',
                'item_subtotal': float(cart_item.subtotal),
                'cart_total': float(cart.total),
                'cart_count': cart.cantidad_productos,
                'message': 'Carrito actualizado.'
            })

        except (Carrito.DoesNotExist, ItemCarrito.DoesNotExist, Producto.DoesNotExist) as e:
            logger.error(f'Error al actualizar carrito: {str(e)}')
            return JsonResponse({
                'status': 'error',
                'message': 'Error al actualizar el carrito.'
            }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
