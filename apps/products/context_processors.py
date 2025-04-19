from .models import Categoria

def categories(request):
    """
    Context processor para tener las categorías disponibles en todas las plantillas.
    """
    return {
        'categories': Categoria.objects.filter(activa=True)
    }