# apps/cart/context_processors.py
from .models import Carrito

def cart_context(request):
    """
    Contexto para cargar información del carrito en todas las páginas.
    """
    cart_count = 0
    cart_total = 0
    cart_items = []
    cart = None
    
    if request.user.is_authenticated:
        try:
            cart, created = Carrito.objects.get_or_create(usuario=request.user)
            cart_items = cart.items.all().select_related('producto')
            cart_count = cart.cantidad_productos
            cart_total = cart.total
        except Exception as e:
            # Si hay algún error, simplemente logueamos y continuamos con valores predeterminados
            print(f"Error al obtener el carrito: {e}")
    
    return {
        'cart_count': cart_count,
        'cart_total': cart_total,
        'cart_items': cart_items,
        'cart': cart  # Añadir el objeto carrito completo
    }