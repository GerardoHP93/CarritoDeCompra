def cart_context(request):
    """
    Contexto para cargar información del carrito en todas las páginas.
    Esta función será completada en la fase de implementación del carrito.
    """
    # Por ahora, solo devolvemos un diccionario vacío.
    # En la fase del carrito, esto devolverá información real.
    return {
        'cart_count': 0,
        'cart_total': 0,
    }