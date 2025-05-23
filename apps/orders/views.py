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
from .forms import DireccionEnvioForm, MetodoPagoForm, StripePaymentForm
from apps.cart.models import Carrito
from apps.users.models import DireccionEnvio
from apps.products.models import CalificacionProducto
from apps.products.forms import CalificacionProductoForm
from django.conf import settings
from .stripe_utils import create_payment_intent, retrieve_payment_intent, handle_payment_success

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
        # Obtener los items del carrito para mostrarlos en la vista
        cart_items = carrito.items.all().select_related('producto')
    except Carrito.DoesNotExist:
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de continuar.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Verificar si hay una sesión de checkout activa
    orden_id = request.session.get('orden_id')
    if orden_id:
        try:
            # Si hay una orden existente, verificar si ya está en proceso
            orden = Orden.objects.get(id=orden_id, usuario=request.user, estado='pendiente')
            
            # MODIFICADO: No redirigir automáticamente al siguiente paso
            # Solo verificar si el carrito ha cambiado
            if not verificar_carrito_orden(carrito, orden):
                logger.info(f"Carrito ha cambiado, limpiando sesión de checkout para usuario {request.user.username}")
                limpiar_sesion_checkout(request)
                orden_id = None
                
        except Orden.DoesNotExist:
            # Si la orden no existe o no pertenece al usuario, eliminar la sesión
            limpiar_sesion_checkout(request)
            orden_id = None
    
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
        'active_step': 'direccion',
        'cart': carrito,  # Añadir el carrito al contexto
        'cart_items': cart_items  # Añadir los items del carrito al contexto
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
        # Obtener el carrito y los items para mostrarlos en la vista
        carrito = Carrito.objects.get(usuario=request.user)
        cart_items = carrito.items.all().select_related('producto')
        
        # Verificar si los productos en la orden y el carrito son los mismos
        if not verificar_carrito_orden(carrito, orden):
            logger.info(f"Carrito ha cambiado, limpiando sesión de checkout para usuario {request.user.username}")
            limpiar_sesion_checkout(request)
            return redirect('orders:checkout_direccion')
            
    except Orden.DoesNotExist:
        limpiar_sesion_checkout(request)
        messages.error(request, "Ha ocurrido un error con tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
        return redirect('cart:cart_detail')
    except Carrito.DoesNotExist:
        # Manejar el caso en que no haya carrito
        carrito = None
        cart_items = []
        messages.warning(request, "Tu carrito está vacío. Agrega productos antes de continuar.", extra_tags='toast')
        return redirect('cart:cart_detail')
    
    # Siempre crear un nuevo PaymentIntent en cada carga de la página
    logger.info(f"Creando PaymentIntent para orden #{orden.id} por ${carrito.total}")
    stripe_payment_intent = create_payment_intent(
        amount=float(carrito.total),
        metadata={
            'order_id': orden.id,
            'customer_id': request.user.id,
            'customer_email': request.user.email
        }
    )
    
    if 'error' in stripe_payment_intent:
        logger.error(f"Error al crear PaymentIntent: {stripe_payment_intent['error']}")
        messages.error(request, "Error al inicializar el sistema de pagos. Por favor, intenta de nuevo más tarde.", extra_tags='toast')
    else:
        logger.info(f"PaymentIntent creado exitosamente: {stripe_payment_intent['id']}")
        request.session['stripe_payment_intent_id'] = stripe_payment_intent['id']
    
    if request.method == 'POST':
        logger.debug(f"POST recibido para checkout_pago: {request.POST}")
        
        # Cuando usamos Stripe Elements, no necesitamos validar los campos de tarjeta normales
        if 'metodo_pago' in request.POST and request.POST['metodo_pago'] == 'tarjeta':
            # Para tarjetas, solo necesitamos que el método de pago sea válido y los datos de Stripe
            # Obtener los valores no vacíos de los campos de payment_intent_id y payment_method_id
            payment_intent_ids = [pid for pid in request.POST.getlist('payment_intent_id') if pid.strip()]
            payment_method_ids = [pmid for pmid in request.POST.getlist('payment_method_id') if pmid.strip()]
            
            payment_intent_id = payment_intent_ids[0] if payment_intent_ids else None
            payment_method_id = payment_method_ids[0] if payment_method_ids else None
            
            logger.info(f"Payment Intent ID: {payment_intent_id}, Payment Method ID: {payment_method_id}")
            
            if payment_intent_id and payment_method_id:
                logger.info(f"Procesando pago con tarjeta: {payment_intent_id}")
                
                # Verificar estado del pago
                payment_result = retrieve_payment_intent(payment_intent_id)
                if 'error' not in payment_result and payment_result.get('status') == 'succeeded':
                    # Pago exitoso con Stripe
                    logger.info(f"Pago exitoso con tarjeta: {payment_intent_id}")
                    
                    # Datos para la sesión
                    pago_data = {
                        'metodo_pago': 'tarjeta',
                        'tipo_tarjeta': 'visa',  # Valor por defecto
                        'numero_tarjeta': '•••• •••• •••• 4242',  # Por defecto para pruebas
                        'titular_tarjeta': request.POST.get('titular_tarjeta', request.user.get_full_name()),
                        'referencia_pago': payment_intent_id
                    }
                    
                    # Guardar en la sesión
                    request.session['pago_completo'] = pago_data
                    
                    # Actualizar la orden en la base de datos
                    orden.metodo_pago = 'tarjeta'
                    orden.referencia_pago = payment_intent_id
                    orden.save()
                    
                    # Redirigir al siguiente paso
                    return redirect('orders:checkout_resumen')
                else:
                    # Error en el pago
                    error_msg = payment_result.get('error', 'Error en el procesamiento del pago')
                    logger.error(f"Error en pago con tarjeta: {error_msg}")
                    messages.error(request, f"Error en el pago: {error_msg}", extra_tags='toast')
            else:
                logger.warning(f"Datos de Stripe incompletos: payment_intent_id={payment_intent_id}, payment_method_id={payment_method_id}")
                messages.error(request, "Datos de pago incompletos. Por favor, intenta de nuevo con otra tarjeta.", extra_tags='toast')
        
        # Validación normal del formulario para otros métodos de pago
        form = MetodoPagoForm(request.POST)
        stripe_form = StripePaymentForm(request.POST)
        
        if form.is_valid():
            metodo_pago = form.cleaned_data['metodo_pago']
            
            # Para PayPal
            if metodo_pago == 'paypal':
                # Simulación de pago con PayPal
                paypal_reference = f"PP-{uuid.uuid4().hex[:10].upper()}"
                logger.info(f"Pago simulado con PayPal: {paypal_reference}")
                
                pago_data = {
                    'metodo_pago': 'paypal',
                    'referencia_pago': paypal_reference
                }
                
                # Guardar en la sesión
                request.session['pago_completo'] = pago_data
                
                # Actualizar la orden en la base de datos
                orden.metodo_pago = 'paypal'
                orden.referencia_pago = paypal_reference
                orden.save()
                
                # Redirigir al siguiente paso
                return redirect('orders:checkout_resumen')
        else:
            logger.warning(f"Formulario inválido: {form.errors}")
    else:
        form = MetodoPagoForm()
        stripe_form = StripePaymentForm()
    
    context = {
        'form': form,
        'stripe_form': stripe_form,
        'active_step': 'pago',
        'cart': carrito,
        'cart_items': cart_items,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'stripe_client_secret': stripe_payment_intent.get('client_secret') if stripe_payment_intent else None,
        'stripe_payment_intent_id': stripe_payment_intent.get('id') if stripe_payment_intent else None,
    }
    
    logger.debug(f"Renderizando checkout_pago con context: stripe_client_secret={bool(context['stripe_client_secret'])}, stripe_publishable_key={bool(context['stripe_publishable_key'])}")
    
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
        # Obtener el carrito
        carrito = Carrito.objects.get(usuario=request.user)
        items_carrito = carrito.items.all().select_related('producto')
        
        # NUEVO: Verificar si los productos en la orden y el carrito son los mismos
        if not verificar_carrito_orden(carrito, orden):
            logger.info(f"Carrito ha cambiado, limpiando sesión de checkout para usuario {request.user.username}")
            limpiar_sesion_checkout(request)
            return redirect('orders:checkout_direccion')
            
    except Orden.DoesNotExist:
        limpiar_sesion_checkout(request)
        messages.error(request, "Ha ocurrido un error con tu orden. Por favor, inténtalo de nuevo.", extra_tags='toast')
        return redirect('cart:cart_detail')
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
                orden.total = carrito.total  # Asegurarse de que el total esté actualizado
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
                limpiar_sesion_checkout(request)
                
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
        'active_step': 'resumen',
        'cart': carrito  # Añadir el carrito al contexto
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

def limpiar_sesion_checkout(request):
    """
    Limpia las variables de sesión relacionadas con el proceso de checkout.
    """
    if 'orden_id' in request.session:
        del request.session['orden_id']
    if 'direccion_completa' in request.session:
        del request.session['direccion_completa']
    if 'pago_completo' in request.session:
        del request.session['pago_completo']
    # Añadir limpieza de datos de Stripe
    if 'stripe_payment_intent_id' in request.session:
        del request.session['stripe_payment_intent_id']

def verificar_carrito_orden(carrito, orden):
    """
    Verifica si los productos en el carrito son consistentes con la orden.
    Retorna True si son consistentes, False si hay diferencias.
    
    Esta función es útil para detectar si el usuario ha modificado su carrito
    después de iniciar el proceso de checkout.
    """
    # Como no tenemos detalles en la orden hasta que se confirma, comparamos el total
    # Si el total es diferente, significa que el carrito ha cambiado
    return abs(carrito.total - orden.total) < 0.01  # Comparar con un pequeño margen de error para evitar problemas de redondeo

# En apps/orders/views.py - agregar estas funciones
@login_required
def confirmar_recepcion(request, numero_orden):
    """
    Vista para confirmar que el usuario ha recibido el pedido.
    """
    orden = get_object_or_404(Orden, numero_orden=numero_orden, usuario=request.user)
    
    if orden.estado != 'entregado' and orden.estado != 'enviado':
        messages.warning(request, "Solo puedes confirmar la recepción de pedidos que estén en estado 'Enviado' o 'Entregado'.", extra_tags='toast')
        return redirect('orders:detalle_orden', numero_orden=numero_orden)
    
    if request.method == 'POST':
        try:
            orden.recibido = True
            orden.fecha_recepcion = timezone.now()
            # Actualizar estado a entregado si estaba en enviado
            if orden.estado == 'enviado':
                orden.estado = 'entregado'
            orden.save()
            
            logger.info(f"Usuario {request.user.username} confirmó la recepción del pedido #{orden.numero_orden}")
            messages.success(request, "¡Gracias! Has confirmado la recepción de tu pedido.", extra_tags='toast')
            
            # Redirigir a la página de valoraciones
            return redirect('orders:valorar_productos', numero_orden=numero_orden)
            
        except Exception as e:
            logger.error(f"Error al confirmar recepción: {str(e)}")
            messages.error(request, "Ha ocurrido un error al confirmar la recepción.", extra_tags='toast')
    
    return redirect('orders:detalle_orden', numero_orden=numero_orden)

@login_required
def valorar_productos(request, numero_orden):
    """
    Vista para valorar los productos de una orden recibida.
    """
    orden = get_object_or_404(Orden, numero_orden=numero_orden, usuario=request.user, recibido=True)
    detalles = orden.detalles.all().select_related('producto')
    
    # Verificar si el usuario ya ha valorado algún producto
    productos_ids = [detalle.producto.id for detalle in detalles]
    valoraciones_existentes = CalificacionProducto.objects.filter(
        producto_id__in=productos_ids,
        cliente=request.user.cliente
    )
    
    # Mapear producto_id -> valoración para fácil acceso
    valoraciones_map = {val.producto_id: val for val in valoraciones_existentes}
    
    # Preparar los detalles con información de valoración
    detalles_info = []
    for detalle in detalles:
        # Aquí está el cambio importante: inicializar el formulario con los valores existentes
        if detalle.producto.id in valoraciones_map:
            valoracion = valoraciones_map[detalle.producto.id]
            form = CalificacionProductoForm(
                prefix=f'producto_{detalle.producto.id}',
                initial={
                    'puntuacion': valoracion.puntuacion,
                    'comentario': valoracion.comentario
                }
            )
        else:
            form = CalificacionProductoForm(prefix=f'producto_{detalle.producto.id}')
        
        info = {
            'detalle': detalle,
            'valorado': detalle.producto.id in valoraciones_map,
            'valoracion': valoraciones_map.get(detalle.producto.id, None),
            'form': form
        }
        detalles_info.append(info)
    
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        if producto_id:
            try:
                producto_id = int(producto_id)
                # Verificar que el producto pertenece a la orden
                if producto_id in productos_ids:
                    # Verificar si ya existe una valoración
                    try:
                        valoracion = CalificacionProducto.objects.get(
                            producto_id=producto_id,
                            cliente=request.user.cliente
                        )
                        form = CalificacionProductoForm(
                            request.POST,
                            prefix=f'producto_{producto_id}',
                            instance=valoracion
                        )
                    except CalificacionProducto.DoesNotExist:
                        form = CalificacionProductoForm(
                            request.POST,
                            prefix=f'producto_{producto_id}'
                        )
                    
                    if form.is_valid():
                        valoracion = form.save(commit=False)
                        valoracion.producto_id = producto_id
                        valoracion.cliente = request.user.cliente
                        valoracion.save()
                        
                        logger.info(f"Usuario {request.user.username} valoró el producto {producto_id} con {valoracion.puntuacion} estrellas")
                        messages.success(request, "¡Gracias por tu valoración!", extra_tags='toast')
                        return redirect('orders:valorar_productos', numero_orden=numero_orden)
                    else:
                        messages.warning(request, "Por favor corrige los errores en el formulario.", extra_tags='toast')
                else:
                    messages.warning(request, "El producto seleccionado no pertenece a esta orden.", extra_tags='toast')
            except ValueError:
                messages.error(request, "ID de producto inválido.", extra_tags='toast')
    
    context = {
        'orden': orden,
        'detalles_info': detalles_info,
        'titulo': 'Valorar Productos',
    }
    
    return render(request, 'orders/valorar_productos.html', context)