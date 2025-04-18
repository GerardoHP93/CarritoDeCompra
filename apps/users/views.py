import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from .forms import (
    UserRegisterForm, UserLoginForm, UserUpdateForm, 
    ClienteUpdateForm, DireccionEnvioForm
)
from .models import DireccionEnvio

# Configurar el logger
logger = logging.getLogger('apps.users')

def register(request):
    """
    Vista para el registro de nuevos usuarios.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'¡Cuenta creada para {username}! Ya puedes iniciar sesión.')
                logger.info(f"Usuario {username} registrado exitosamente")
                
                # Iniciar sesión automáticamente
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                messages.info(request, f'¡Bienvenido/a, {username}!')
                return redirect('core:home')
            except Exception as e:
                logger.error(f"Error en el registro: {str(e)}")
                messages.error(request, 'Ha ocurrido un error en el registro. Por favor, inténtalo de nuevo.')
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """
    Vista para el inicio de sesión de usuarios.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
        
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info(f"Usuario {username} inició sesión")
                messages.success(request, f'¡Bienvenido/a de nuevo, {username}!')
                
                # Redirigir a la página que el usuario intentaba acceder
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('core:home')
        else:
            logger.warning(f"Intento de inicio de sesión fallido")
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    """
    Vista para cerrar sesión.
    """
    logout(request)
    messages.info(request, '¡Has cerrado sesión correctamente!')
    logger.info(f"Usuario {request.user.username} cerró sesión")
    return redirect('core:home')

@login_required
def profile(request):
    """
    Vista para mostrar el perfil del usuario.
    """
    # Obtener las direcciones del usuario
    direcciones = DireccionEnvio.objects.filter(cliente=request.user.cliente)
    
    context = {
        'user': request.user,
        'cliente': request.user.cliente,
        'direcciones': direcciones
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    """
    Vista para editar el perfil del usuario.
    """
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        c_form = ClienteUpdateForm(request.POST, request.FILES, instance=request.user.cliente)
        
        if u_form.is_valid() and c_form.is_valid():
            try:
                u_form.save()
                c_form.save()
                messages.success(request, '¡Tu perfil ha sido actualizado!')
                logger.info(f"Usuario {request.user.username} actualizó su perfil")
                return redirect('users:profile')
            except Exception as e:
                logger.error(f"Error al actualizar perfil: {str(e)}")
                messages.error(request, 'Ha ocurrido un error al actualizar tu perfil.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        c_form = ClienteUpdateForm(instance=request.user.cliente)
    
    context = {
        'u_form': u_form,
        'c_form': c_form
    }
    return render(request, 'users/edit_profile.html', context)

@login_required
def addresses(request):
    """
    Vista para mostrar las direcciones del usuario.
    """
    direcciones = DireccionEnvio.objects.filter(cliente=request.user.cliente)
    return render(request, 'users/addresses.html', {'direcciones': direcciones})

@login_required
def add_address(request):
    """
    Vista para agregar una nueva dirección.
    """
    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST)
        if form.is_valid():
            try:
                direccion = form.save(commit=False)
                direccion.cliente = request.user.cliente
                
                # Si es la primera dirección o se marca como principal
                if form.cleaned_data.get('es_principal') or not DireccionEnvio.objects.filter(cliente=request.user.cliente).exists():
                    # Desmarcar cualquier otra dirección principal
                    DireccionEnvio.objects.filter(cliente=request.user.cliente, es_principal=True).update(es_principal=False)
                    direccion.es_principal = True
                
                direccion.save()
                messages.success(request, '¡Dirección agregada correctamente!')
                logger.info(f"Usuario {request.user.username} agregó una nueva dirección")
                return redirect('users:addresses')
            except Exception as e:
                logger.error(f"Error al agregar dirección: {str(e)}")
                messages.error(request, 'Ha ocurrido un error al agregar la dirección.')
    else:
        form = DireccionEnvioForm()
    
    return render(request, 'users/address_form.html', {'form': form, 'title': 'Agregar Dirección'})

@login_required
def edit_address(request, pk):
    """
    Vista para editar una dirección existente.
    """
    direccion = get_object_or_404(DireccionEnvio, pk=pk, cliente=request.user.cliente)
    
    if request.method == 'POST':
        form = DireccionEnvioForm(request.POST, instance=direccion)
        if form.is_valid():
            try:
                direccion = form.save(commit=False)
                
                # Si se marca como principal, desmarcar las otras
                if form.cleaned_data.get('es_principal'):
                    DireccionEnvio.objects.filter(cliente=request.user.cliente, es_principal=True).exclude(pk=pk).update(es_principal=False)
                    direccion.es_principal = True
                
                direccion.save()
                messages.success(request, '¡Dirección actualizada correctamente!')
                logger.info(f"Usuario {request.user.username} actualizó una dirección")
                return redirect('users:addresses')
            except Exception as e:
                logger.error(f"Error al actualizar dirección: {str(e)}")
                messages.error(request, 'Ha ocurrido un error al actualizar la dirección.')
    else:
        form = DireccionEnvioForm(instance=direccion)
    
    return render(request, 'users/address_form.html', {'form': form, 'title': 'Editar Dirección'})

@login_required
def delete_address(request, pk):
    """
    Vista para eliminar una dirección.
    """
    direccion = get_object_or_404(DireccionEnvio, pk=pk, cliente=request.user.cliente)
    
    try:
        # Si la dirección era principal y hay otras direcciones, hacer otra principal
        if direccion.es_principal:
            otra_direccion = DireccionEnvio.objects.filter(cliente=request.user.cliente).exclude(pk=pk).first()
            if otra_direccion:
                otra_direccion.es_principal = True
                otra_direccion.save()
        
        direccion.delete()
        messages.success(request, '¡Dirección eliminada correctamente!')
        logger.info(f"Usuario {request.user.username} eliminó una dirección")
    except Exception as e:
        logger.error(f"Error al eliminar dirección: {str(e)}")
        messages.error(request, 'Ha ocurrido un error al eliminar la dirección.')
    
    return redirect('users:addresses')

@login_required
def set_default_address(request, pk):
    """
    Vista para establecer una dirección como principal.
    """
    try:
        # Desmarcar todas las direcciones principales
        DireccionEnvio.objects.filter(cliente=request.user.cliente, es_principal=True).update(es_principal=False)
        
        # Marcar la seleccionada como principal
        direccion = get_object_or_404(DireccionEnvio, pk=pk, cliente=request.user.cliente)
        direccion.es_principal = True
        direccion.save()
        
        messages.success(request, '¡Dirección establecida como principal!')
        logger.info(f"Usuario {request.user.username} cambió su dirección principal")
    except Exception as e:
        logger.error(f"Error al establecer dirección principal: {str(e)}")
        messages.error(request, 'Ha ocurrido un error al establecer la dirección como principal.')
    
    return redirect('users:addresses')