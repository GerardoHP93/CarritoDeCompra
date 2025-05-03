from django.contrib import admin
from .models import Categoria, DetallePedidoProveedor, PedidoProveedor, Proveedor, Producto, ImagenProducto, CalificacionProducto

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
    
# apps/products/admin.py
# Añadir al final del archivo

class DetallePedidoProveedorInline(admin.TabularInline):
    model = DetallePedidoProveedor
    extra = 0
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']

@admin.register(PedidoProveedor)
class PedidoProveedorAdmin(admin.ModelAdmin):
    list_display = ('numero_pedido', 'proveedor', 'total', 'estado', 'fecha_solicitud', 'fecha_estimada_llegada')
    list_filter = ('estado', 'proveedor', 'fecha_solicitud')
    search_fields = ('numero_pedido', 'proveedor__nombre')
    readonly_fields = ('numero_pedido', 'fecha_solicitud', 'fecha_actualizacion')
    inlines = [DetallePedidoProveedorInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_pedido', 'proveedor', 'estado')
        }),
        ('Información de Entrega', {
            'fields': ('fecha_estimada_llegada',)
        }),
        ('Información Financiera', {
            'fields': ('total',)
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_actualizacion')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )