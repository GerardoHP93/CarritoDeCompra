# apps/products/inventory_views.py
# Crear este nuevo archivo para las vistas de gestión de inventario

import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum, F
from django.http import JsonResponse

from .models import Producto, Proveedor, PedidoProveedor, DetallePedidoProveedor
from .forms import PedidoProveedorForm, DetallePedidoProveedorFormSet

# Configurar el logger
logger = logging.getLogger('apps.products')

# Función para verificar si el usuario es administrador
def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def dashboard_inventario(request):
    """
    Dashboard principal de gestión de inventario para administradores.
    Muestra productos con stock bajo, pedidos en proceso, etc.
    """
    # Productos con stock bajo (menor a 10 unidades)
    productos_stock_bajo = Producto.objects.filter(stock__lt=10, activo=True).order_by('stock')
    
    # Pedidos pendientes o en tránsito
    pedidos_pendientes = PedidoProveedor.objects.filter(
        estado__in=['pendiente', 'pagado', 'en_transito']
    ).order_by('fecha_solicitud')
    
    # Productos más vendidos (implementar cuando tengamos datos de ventas)
    
    context = {
        'productos_stock_bajo': productos_stock_bajo,
        'pedidos_pendientes': pedidos_pendientes,
        'title': 'Dashboard de Inventario'
    }
    
    return render(request, 'products/inventory/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def lista_pedidos_proveedor(request):
    """
    Lista de todos los pedidos a proveedores.
    """
    pedidos = PedidoProveedor.objects.all().order_by('-fecha_solicitud')
    
    context = {
        'pedidos': pedidos,
        'title': 'Pedidos a Proveedores'
    }
    
    return render(request, 'products/inventory/lista_pedidos.html', context)

# Actualización en apps/products/inventory_views.py

@login_required
@user_passes_test(is_admin)
def detalle_pedido_proveedor(request, numero_pedido):
    """
    Detalles de un pedido específico a proveedor.
    """
    pedido = get_object_or_404(PedidoProveedor, numero_pedido=numero_pedido)
    detalles = pedido.detalles.all().select_related('producto')
    
    # Para pedidos recibidos, calculamos el stock anterior para mostrarlo en la vista
    if pedido.estado == 'recibido':
        for detalle in detalles:
            # Calculamos el stock anterior restando la cantidad recibida del stock actual
            detalle.stock_anterior = detalle.producto.stock - detalle.cantidad
    
    context = {
        'pedido': pedido,
        'detalles': detalles,
        'title': f'Pedido #{pedido.numero_pedido}'
    }
    
    return render(request, 'products/inventory/detalle_pedido.html', context)

# Modificación en apps/products/inventory_views.py
@login_required
@user_passes_test(is_admin)
def crear_pedido_proveedor(request):
    """
    Creación de un nuevo pedido a proveedor.
    """
    # Si hay parámetros en la URL, preseleccionar proveedor y producto
    proveedor_id = request.GET.get('proveedor')
    producto_id = request.GET.get('producto')
    
    if request.method == 'POST':
        form = PedidoProveedorForm(request.POST)
        formset = DetallePedidoProveedorFormSet(request.POST, prefix='detalles')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar pedido sin commit para poder modificarlo
                    pedido = form.save(commit=False)
                    
                    # La fecha estimada de llegada se calcula automáticamente en save()
                    
                    # Primero guardar el pedido para obtener un ID
                    pedido.save()
                    
                    # Guardar detalles y calcular total
                    total = 0
                    for detalle_form in formset:
                        if detalle_form.cleaned_data and not detalle_form.cleaned_data.get('DELETE', False):
                            if 'producto' in detalle_form.cleaned_data and 'cantidad' in detalle_form.cleaned_data and 'precio_unitario' in detalle_form.cleaned_data:
                                detalle = detalle_form.save(commit=False)
                                detalle.pedido = pedido
                                detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                                detalle.save()
                                total += detalle.subtotal
                    
                    # Actualizar total del pedido
                    pedido.total = total
                    pedido.save()
                    
                    logger.info(f"Pedido a proveedor #{pedido.numero_pedido} creado")
                    messages.success(request, f'Pedido #{pedido.numero_pedido} creado correctamente')
                    
                    return redirect('products:lista_pedidos_proveedor')
            except Exception as e:
                logger.error(f"Error al crear pedido: {str(e)}")
                messages.error(request, f'Error al crear pedido: {str(e)}')
    else:
        # Inicializar formulario
        initial = {}
        if proveedor_id:
            initial['proveedor'] = proveedor_id
            
        form = PedidoProveedorForm(initial=initial)
        formset = DetallePedidoProveedorFormSet(prefix='detalles')
        
        # Si hay un producto seleccionado, prellenar el primer formulario del formset
        if producto_id and proveedor_id:
            try:
                producto = Producto.objects.get(id=producto_id, proveedor_id=proveedor_id)
                # Inicializar un formset con datos iniciales para el primer formulario
                formset = DetallePedidoProveedorFormSet(
                    initial=[{
                        'producto': producto.id,
                        'cantidad': 10,  # Cantidad sugerida por defecto
                        'precio_unitario': float(producto.precio)
                    }],
                    prefix='detalles'
                )
            except Producto.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Nuevo Pedido a Proveedor'
    }
    
    return render(request, 'products/inventory/crear_pedido.html', context)

# Modificación en apps/products/inventory_views.py
# Versión mejorada de la función editar_pedido_proveedor

@login_required
@user_passes_test(is_admin)
def editar_pedido_proveedor(request, numero_pedido):
    """
    Vista para editar un pedido existente a proveedor.
    """
    pedido = get_object_or_404(PedidoProveedor, numero_pedido=numero_pedido)
    
    # No permitir editar pedidos que ya no están en estado pendiente
    if pedido.estado != 'pendiente':
        messages.warning(request, f'No se puede editar un pedido en estado {pedido.get_estado_display()}')
        return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
    
    if request.method == 'POST':
        form = PedidoProveedorForm(request.POST, instance=pedido)
        formset = DetallePedidoProveedorFormSet(request.POST, instance=pedido, prefix='detalles')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Guardar pedido
                    pedido = form.save()
                    
                    # Guardar formset y recalcular total
                    formset.save()
                    
                    # Recalcular total del pedido sumando subtotales de todos los detalles activos
                    total = 0
                    
                    for detalle in pedido.detalles.all():
                        # Asegurarse de que los subtotales estén actualizados
                        detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                        detalle.save()
                        total += detalle.subtotal
                    
                    # Actualizar total del pedido
                    pedido.total = total
                    pedido.save()
                    
                    logger.info(f"Pedido a proveedor #{pedido.numero_pedido} actualizado")
                    messages.success(request, f'Pedido #{pedido.numero_pedido} actualizado correctamente')
                    
                    return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
            except Exception as e:
                logger.error(f"Error al actualizar pedido: {str(e)}")
                messages.error(request, f'Error al actualizar pedido: {str(e)}')
    else:
        form = PedidoProveedorForm(instance=pedido)
        formset = DetallePedidoProveedorFormSet(instance=pedido, prefix='detalles')
    
    context = {
        'form': form,
        'formset': formset,
        'pedido': pedido,
        'title': f'Editar Pedido #{pedido.numero_pedido}'
    }
    
    return render(request, 'products/inventory/editar_pedido.html', context)

@login_required
@user_passes_test(is_admin)
def cancelar_pedido_proveedor(request, numero_pedido):
    """
    Cancelar un pedido a proveedor.
    """
    pedido = get_object_or_404(PedidoProveedor, numero_pedido=numero_pedido)
    
    # No permitir cancelar pedidos que ya están recibidos
    if pedido.estado == 'recibido':
        messages.warning(request, 'No se puede cancelar un pedido ya recibido')
        return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
    
    if request.method == 'POST':
        try:
            pedido.estado = 'cancelado'
            pedido.save()
            
            logger.info(f"Pedido a proveedor #{pedido.numero_pedido} cancelado")
            messages.success(request, f'Pedido #{pedido.numero_pedido} cancelado correctamente')
            
            return redirect('products:lista_pedidos_proveedor')
        except Exception as e:
            logger.error(f"Error al cancelar pedido: {str(e)}")
            messages.error(request, f'Error al cancelar pedido: {str(e)}')
    
    context = {
        'pedido': pedido,
        'title': f'Cancelar Pedido #{pedido.numero_pedido}'
    }
    
    return render(request, 'products/inventory/cancelar_pedido.html', context)

@login_required
@user_passes_test(is_admin)
def pagar_pedido_proveedor(request, numero_pedido):
    """
    Simular el pago de un pedido a proveedor.
    """
    pedido = get_object_or_404(PedidoProveedor, numero_pedido=numero_pedido)
    
    # No permitir pagar pedidos que no están en estado pendiente
    if pedido.estado != 'pendiente':
        messages.warning(request, f'No se puede pagar un pedido en estado {pedido.get_estado_display()}')
        return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
    
    if request.method == 'POST':
        try:
            pedido.estado = 'pagado'
            pedido.save()
            
            logger.info(f"Pedido a proveedor #{pedido.numero_pedido} pagado")
            messages.success(request, f'Pedido #{pedido.numero_pedido} pagado correctamente')
            
            return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
        except Exception as e:
            logger.error(f"Error al pagar pedido: {str(e)}")
            messages.error(request, f'Error al pagar pedido: {str(e)}')
    
    context = {
        'pedido': pedido,
        'title': f'Pagar Pedido #{pedido.numero_pedido}'
    }
    
    return render(request, 'products/inventory/pagar_pedido.html', context)

# Actualización en apps/products/inventory_views.py

@login_required
@user_passes_test(is_admin)
def recibir_pedido_proveedor(request, numero_pedido):
    """
    Marcar un pedido como recibido y actualizar el stock.
    """
    pedido = get_object_or_404(PedidoProveedor, numero_pedido=numero_pedido)
    
    # Solo permitir recibir pedidos que están en estado pagado o en tránsito
    if pedido.estado not in ['pagado', 'en_transito']:
        messages.warning(request, f'No se puede recibir un pedido en estado {pedido.get_estado_display()}')
        return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Si está en estado pagado, primero pasarlo a en_transito
                if pedido.estado == 'pagado':
                    pedido.estado = 'en_transito'
                    pedido.save()
                    
                    logger.info(f"Pedido a proveedor #{pedido.numero_pedido} marcado en tránsito")
                    messages.success(request, f'Pedido #{pedido.numero_pedido} marcado como en tránsito')
                    
                    return redirect('products:detalle_pedido_proveedor', numero_pedido=numero_pedido)
                
                # Si ya está en tránsito, marcarlo como recibido y actualizar stock
                pedido.estado = 'recibido'
                pedido.save()
                
                # Actualizar stock de productos - CORREGIDO
                for detalle in pedido.detalles.all():
                    producto = detalle.producto
                    # Guardar el stock anterior para el log
                    stock_anterior = producto.stock
                    # Actualizar el stock
                    producto.stock += detalle.cantidad
                    producto.save()
                    logger.info(f"Stock actualizado para {producto.nombre}: {stock_anterior} + {detalle.cantidad} = {producto.stock} unidades")
                
                logger.info(f"Pedido a proveedor #{pedido.numero_pedido} recibido y stock actualizado")
                messages.success(request, f'Pedido #{pedido.numero_pedido} recibido correctamente y stock actualizado')
                
                return redirect('products:lista_pedidos_proveedor')
        except Exception as e:
            logger.error(f"Error al recibir pedido: {str(e)}")
            messages.error(request, f'Error al recibir pedido: {str(e)}')
    
    context = {
        'pedido': pedido,
        'detalles': pedido.detalles.all().select_related('producto'),
        'title': f'Recibir Pedido #{pedido.numero_pedido}'
    }
    
    return render(request, 'products/inventory/recibir_pedido.html', context)

@login_required
@user_passes_test(is_admin)
def obtener_productos_proveedor(request, proveedor_id):
    """
    Vista AJAX para obtener los productos de un proveedor específico.
    """
    try:
        productos = Producto.objects.filter(
            proveedor_id=proveedor_id, 
            activo=True
        ).values('id', 'nombre', 'precio', 'stock')
        
        return JsonResponse({'productos': list(productos)})
    except Exception as e:
        logger.error(f"Error al obtener productos del proveedor: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)