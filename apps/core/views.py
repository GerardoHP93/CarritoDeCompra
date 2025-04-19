import logging
from django.shortcuts import render
from apps.products.models import Categoria, Producto

# Configurar el logger
logger = logging.getLogger('apps.core')

def home(request):
    """
    Vista para la página principal del market digital.
    """
    logger.debug('Acceso a la página de inicio')
    
    # Obtener categorías activas
    categories = Categoria.objects.filter(activa=True)
    
    # Obtener productos destacados
    featured_products = Producto.objects.filter(activo=True, destacado=True)[:6]
    
    context = {
        'categories': categories,
        'featured_products': featured_products
    }
    
    return render(request, 'core/home.html', context)

def about(request):
    """
    Vista para la página "Quiénes somos".
    """
    logger.debug('Acceso a la página "Quiénes somos"')
    return render(request, 'core/about.html')

def contact(request):
    """
    Vista para la página de contacto.
    """
    logger.debug('Acceso a la página de contacto')
    return render(request, 'core/contact.html')