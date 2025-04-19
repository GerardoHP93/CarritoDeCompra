from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Incluimos las URLs de nuestras aplicaciones
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('products/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),  # Añadir esta línea
    # Las siguientes se implementarán en fases posteriores
    # path('orders/', include('apps.orders.urls')),
]

# Servir archivos estáticos y media durante desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)