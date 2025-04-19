from django.contrib import admin
from .models import Categoria, Proveedor, Producto, ImagenProducto, CalificacionProducto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'email')

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'precio', 'stock', 'categoria', 'proveedor', 'activo', 'destacado')
    list_filter = ('activo', 'destacado', 'categoria', 'proveedor')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [ImagenProductoInline]
    list_editable = ('precio', 'stock', 'activo', 'destacado')

@admin.register(CalificacionProducto)
class CalificacionProductoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'cliente', 'puntuacion', 'fecha_creacion')
    list_filter = ('puntuacion', 'fecha_creacion')
    search_fields = ('producto__nombre', 'cliente__user__username', 'comentario')