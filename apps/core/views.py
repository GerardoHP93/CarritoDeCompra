import logging
from django.shortcuts import render

# Configurar el logger
logger = logging.getLogger('apps.core')

def home(request):
    """
    Vista para la página principal del market digital.
    """
    logger.debug('Acceso a la página de inicio')
    return render(request, 'core/home.html')

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