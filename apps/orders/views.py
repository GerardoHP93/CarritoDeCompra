# apps/orders/views.py
import logging
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction

from .models import Orden, DetalleOrden
from .forms import DireccionEnvioForm, MetodoPagoForm
from apps.cart.models import Carrito
from apps.users.models import DireccionEnvio

# Configurar el logger
logger = logging.getLogger('apps.orders')

@login_required
def checkout_direccion(request):
    """
    Primer paso del checkout: Dirección de envío
    """
    # Verificar si el carrito tiene productos
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        if not carrito.items.exists():
            messages.warning(request, "Tu carrito está vacío. Agrega productos antes de continuar.", extra_tags='toast')
            return redirect('cart:cart_detail')
    except Carrito.DoesNotExist:
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de continuar.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Verificar si hay una sesión de checkout activa
    orden_id = request.session.get('orden_id')
    if orden_id:
        try:
            # Si hay una orden existente, verificar si ya está en proceso
            orden = Orden.objects.get(id=orden_id, usuario=request.user, estado='pendiente')
            if 'direccion_completa' in request.session:
                # Si ya se completó el paso de dirección, redirigir al próximo paso
                return redirect('orders:checkout_pago')
        except Orden.DoesNotExist:
            # Si la orden no existe o no pertenece al usuario, eliminar la sesión
            if 'orden_id' in request.session:
                del request.session['orden_id']
            if 'direccion_completa' in request.session:
                del request.session['direccion_completa']
    
    # Obtener las direcciones guardadas del usuario
    direcciones = DireccionEnvio.objects.filter(cliente=request.user.cliente)
    
    # Inicializar con la dirección principal si existe
    direccion_principal = direcciones.filter(es_principal=True).first()
    initial_data = {}
    if direccion_principal:
        initial_data = {
            'nombre_completo': direccion_principal.nombre_completo,
            'calle': direccion_principal.calle,
            'numero_exterior': direccion_principal.numero_exterior,
            'numero_interior': direccion_principal.numero_interior,
            'colonia': direccion_principal.colonia,
            'ciudad': direccion_principal.ciudad,
            'estado': direccion_principal.estado,
            'codigo_postal': direccion_principal.codigo_postal,
            'pais': direccion_principal.pais,
            'telefono_contacto': direccion_principal.telefono_contacto,
            'usar_direccion_guardada': True,
            'direccion_guardada': direccion_principal.id
        }
    
    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST, user=request.user)
        if form.is_valid():
            # Guardar los datos de dirección en la sesión
            direccion_data = {
                'nombre_completo': form.cleaned_data['nombre_completo'],
                'calle': form.cleaned_data['calle'],
                'numero_exterior': form.cleaned_data['numero_exterior'],
                'numero_interior': form.cleaned_data['numero_interior'],
                'colonia': form.cleaned_data['colonia'],
                'ciudad': form.cleaned_data['ciudad'],
                'estado': form.cleaned_data['estado'],
                'codigo_postal': form.cleaned_data['codigo_postal'],
                'pais': form.cleaned_data['pais'],
                'telefono_contacto': form.cleaned_data['telefono_contacto']
            }
            
            # Si seleccionó usar dirección guardada, obtener esa dirección
            if form.cleaned_data['usar_direccion_guardada'] and form.cleaned_data['direccion_guardada']:
                try:
                    direccion_id = int(form.cleaned_data['direccion_guardada'])
                    direccion = DireccionEnvio.objects.get(id=direccion_id, cliente=request.user.cliente)
                    
                    # Actualizar los datos con la dirección seleccionada
                    direccion_data = {
                        'nombre_completo': direccion.nombre_completo,
                        'calle': direccion.calle,
                        'numero_exterior': direccion.numero_exterior,
                        'numero_interior': direccion.numero_interior,
                        'colonia': direccion.colonia,
                        'ciudad': direccion.ciudad,
                        'estado': direccion.estado,
                        'codigo_postal': direccion.codigo_postal,
                        'pais': direccion.pais,
                        'telefono_contacto': direccion.telefono_contacto
                    }
                except (ValueError, DireccionEnvio.DoesNotExist):
                    pass
            
            # Guardar en la sesión
            request.session['direccion_completa'] = direccion_data
            
            # Crear o actualizar la orden en la base de datos
            if orden_id:
                try:
                    orden = Orden.objects.get(id=orden_id, usuario=request.user, estado='pendiente')
                    # Actualizar los campos de dirección
                    orden.nombre_envio = direccion_data['nombre_completo']
                    orden.direccion_envio = f"{direccion_data['calle']} {direccion_data['numero_exterior']}, {direccion_data['colonia']}"
                    if direccion_data['numero_interior']:
                        orden.direccion_envio += f", Int. {direccion_data['numero_interior']}"
                    orden.ciudad_envio = direccion_data['ciudad']
                    orden.estado_envio = direccion_data['estado']
                    orden.codigo_postal_envio = direccion_data['codigo_postal']
                    orden.pais_envio = direccion_data['pais']
                    orden.telefono_envio = direccion_data['telefono_contacto']
                    orden.save()
                except Orden.DoesNotExist:
                    # Si la orden no existe, crear una nueva
                    orden_id = None
            
            if not orden_id:
                # Calcular el total del carrito
                carrito = Carrito.objects.get(usuario=request.user)
                total = carrito.total
                
                # Crear la orden inicial
                orden = Orden.objects.create(
                    usuario=request.user,
                    estado='pendiente',
                    total=total,
                    nombre_envio=direccion_data['nombre_completo'],
                    direccion_envio=f"{direccion_data['calle']} {direccion_data['numero_exterior']}, {direccion_data['colonia']}",
                    ciudad_envio=direccion_data['ciudad'],
                    estado_envio=direccion_data['estado'],
                    codigo_postal_envio=direccion_data['codigo_postal'],
                    pais_envio=direccion_data['pais'],
                    telefono_envio=direccion_data['telefono_contacto']
                )
                
                # Si hay número interior, agregarlo a la dirección
                if direccion_data['numero_interior']:
                    orden.direccion_envio += f", Int. {direccion_data['numero_interior']}"
                    orden.save()
                
                # Guardar el ID de la orden en la sesión
                request.session['orden_id'] = orden.id
            
            # Redirigir al siguiente paso
            return redirect('orders:checkout_pago')
    else:
        form = DireccionEnvioForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'direcciones': direcciones,
        'active_step': 'direccion'
    }
    
    return render(request, 'orders/checkout_direccion.html', context)

@login_required
def checkout_pago(request):
    """
    Segundo paso del checkout: Método de pago
    """
    # Verificar si ya completó el paso de dirección
    if 'direccion_completa' not in request.session:
        messages.warning(request, "Primero debes completar la información de envío.", extra_tags='toast')
        return redirect('orders:checkout_direccion')
    
    # Verificar si hay una orden en proceso
    orden_id = request.session.get('orden_id')
    if not orden_id:
        messages.error(request, "Ha ocurrido un error con tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    try:
        orden = Orden.objects.get(id=orden_id, usuario=request.user, estado='pendiente')
    except Orden.DoesNotExist:
        if 'orden_id' in request.session:
            del request.session['orden_id']
        if 'direccion_completa' in request.session:
            del request.session['direccion_completa']
        messages.error(request, "Ha ocurrido un error con tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Verificar si ya completó el paso de pago
    if 'pago_completo' in request.session:
        return redirect('orders:checkout_resumen')
    
    if request.method == 'POST':
        form = MetodoPagoForm(request.POST)
        if form.is_valid():
            # Guardar el método de pago en la sesión
            metodo_pago = form.cleaned_data['metodo_pago']
            pago_data = {
                'metodo_pago': metodo_pago
            }
            
            # Si es tarjeta, guardar los datos adicionales
            if metodo_pago == 'tarjeta':
                pago_data['tipo_tarjeta'] = form.cleaned_data['tipo_tarjeta']
                pago_data['numero_tarjeta'] = form.cleaned_data['numero_tarjeta']
                pago_data['titular_tarjeta'] = form.cleaned_data['titular_tarjeta']
                
                # Simular una referencia de pago (para propósitos educativos)
                pago_data['referencia_pago'] = f"REF-{uuid.uuid4().hex[:10].upper()}"
            else:  # PayPal
                # Simular una referencia de pago para PayPal
                pago_data['referencia_pago'] = f"PP-{uuid.uuid4().hex[:10].upper()}"
            
            # Guardar en la sesión
            request.session['pago_completo'] = pago_data
            
            # Actualizar la orden en la base de datos
            orden.metodo_pago = metodo_pago
            orden.referencia_pago = pago_data['referencia_pago']
            orden.save()
            
            # Redirigir al siguiente paso
            return redirect('orders:checkout_resumen')
    else:
        form = MetodoPagoForm()
    
    context = {
        'form': form,
        'active_step': 'pago'
    }
    
    return render(request, 'orders/checkout_pago.html', context)

@login_required
def checkout_resumen(request):
    """
    Tercer paso del checkout: Resumen de la orden
    """
    # Verificar si completó los pasos previos
    if 'direccion_completa' not in request.session or 'pago_completo' not in request.session:
        messages.warning(request, "Debes completar los pasos previos del proceso de compra.", extra_tags='toast')
        return redirect('orders:checkout_direccion')
    
    # Verificar si hay una orden en proceso
    orden_id = request.session.get('orden_id')
    if not orden_id:
        messages.error(request, "Ha ocurrido un error con tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    try:
        orden = Orden.objects.get(id=orden_id, usuario=request.user, estado='pendiente')
    except Orden.DoesNotExist:
        if 'orden_id' in request.session:
            del request.session['orden_id']
        if 'direccion_completa' in request.session:
            del request.session['direccion_completa']
        if 'pago_completo' in request.session:
            del request.session['pago_completo']
        messages.error(request, "Ha ocurrido un error con tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Obtener el carrito
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        items_carrito = carrito.items.all().select_related('producto')
    except Carrito.DoesNotExist:
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de continuar.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Datos para la vista
    direccion_data = request.session.get('direccion_completa', {})
    pago_data = request.session.get('pago_completo', {})
    
    if request.method == 'POST':
        # Confirmar la orden
        with transaction.atomic():
            try:
                # Actualizar la orden con los detalles finales
                orden.estado = 'pagado'  # Cambiar estado a pagado
                orden.fecha_actualizacion = timezone.now()
                orden.save()
                
                # Crear detalles de la orden a partir del carrito
                for item in items_carrito:
                    DetalleOrden.objects.create(
                        orden=orden,
                        producto=item.producto,
                        nombre_producto=item.producto.nombre,
                        precio_unitario=item.producto.precio,
                        cantidad=item.cantidad,
                        subtotal=item.subtotal
                    )
                    
                    # Actualizar stock del producto
                    producto = item.producto
                    producto.stock -= item.cantidad
                    producto.save()
                
                # Vaciar el carrito
                carrito.items.all().delete()
                
                # Limpiar datos de la sesión relacionados con el checkout
                request.session['orden_completada'] = orden.numero_orden
                if 'orden_id' in request.session:
                    del request.session['orden_id']
                if 'direccion_completa' in request.session:
                    del request.session['direccion_completa']
                if 'pago_completo' in request.session:
                    del request.session['pago_completo']
                
                logger.info(f"Orden #{orden.numero_orden} completada exitosamente por el usuario {request.user.username}")
                
                # Redirigir a la página de confirmación
                return redirect('orders:checkout_confirmacion')
                
            except Exception as e:
                logger.error(f"Error al completar la orden: {str(e)}")
                messages.error(request, "Ha ocurrido un error al procesar tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
                return redirect('cart:cart_detail')
    
    context = {
        'orden': orden,
        'items_carrito': items_carrito,
        'direccion_data': direccion_data,
        'pago_data': pago_data,
        'active_step': 'resumen'
    }
    
    return render(request, 'orders/checkout_resumen.html', context)

@login_required
def checkout_confirmacion(request):
    """
    Cuarto paso del checkout: Confirmación de la orden
    """
    # Verificar si hay una orden completada
    numero_orden = request.session.get('orden_completada')
    if not numero_orden:
        messages.warning(request, "No hay una orden completada recientemente.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    try:
        orden = Orden.objects.get(numero_orden=numero_orden, usuario=request.user)
    except Orden.DoesNotExist:
        if 'orden_completada' in request.session:
            del request.session['orden_completada']
        messages.error(request, "No se encontró la orden especificada.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Limpiar la sesión
    if 'orden_completada' in request.session:
        del request.session['orden_completada']
    
    context = {
        'orden': orden,
        'detalles': orden.detalles.all(),
        'active_step': 'confirmacion',
        # Simular fecha estimada de entrega (5 días hábiles desde hoy)
        'fecha_entrega': (timezone.now() + timezone.timedelta(days=5)).date()
    }
    
    return render(request, 'orders/checkout_confirmacion.html', context)

@login_required
def historial_ordenes(request):
    """
    Vista para mostrar el historial de órdenes del usuario.
    """
    ordenes = Orden.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    
    context = {
        'ordenes': ordenes
    }
    
    return render(request, 'orders/historial_ordenes.html', context)

@login_required
def detalle_orden(request, numero_orden):
    """
    Vista para mostrar los detalles de una orden específica.
    """
    orden = get_object_or_404(Orden, numero_orden=numero_orden, usuario=request.user)
    detalles = orden.detalles.all()
    
    context = {
        'orden': orden,
        'detalles': detalles
    }
    
    return render(request, 'orders/detalle_orden.html', context)