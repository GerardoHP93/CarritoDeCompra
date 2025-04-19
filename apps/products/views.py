import logging
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Producto, Categoria, Proveedor

# Configurar el logger
logger = logging.getLogger('apps.products')

def product_list(request, category_slug=None):
    """
    Vista para mostrar el listado de productos, con opción de filtrar por categoría.
    """
    category = None
    categories = Categoria.objects.filter(activa=True)
    products = Producto.objects.filter(activo=True)
    
    # Filtrar por categoría si se proporciona un slug
    if category_slug:
        category = get_object_or_404(Categoria, slug=category_slug, activa=True)
        products = products.filter(categoria=category)
    
    # Paginación de productos
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 productos por página
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    logger.debug(f'Listado de productos: {len(products)} productos mostrados')
    
    context = {
        'category': category,
        'categories': categories,
        'products': products,
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, slug):
    """
    Vista para mostrar los detalles de un producto específico.
    """
    product = get_object_or_404(Producto, slug=slug, activo=True)
    related_products = Producto.objects.filter(categoria=product.categoria).exclude(id=product.id)[:4]
    
    logger.debug(f'Detalle de producto: {product.nombre}')
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)

def product_search(request):
    """
    Vista para buscar productos por nombre o descripción.
    """
    query = request.GET.get('q', '')
    products = []
    
    if query:
        products = Producto.objects.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(categoria__nombre__icontains=query)
        ).filter(activo=True).distinct()
        
        logger.debug(f'Búsqueda de productos por "{query}": {len(products)} resultados')
    
    # Paginación de resultados
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 12)  # 12 productos por página
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'query': query,
        'products': products,
    }
    return render(request, 'products/search_results.html', context)