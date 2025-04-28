# apps/orders/admin.py
from django.contrib import admin
from .models import Orden, DetalleOrden

class DetalleOrdenInline(admin.TabularInline):
    model = DetalleOrden
    extra = 0
    readonly_fields = ['producto', 'nombre_producto', 'precio_unitario', 'cantidad', 'subtotal']

@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ('numero_orden', 'usuario', 'total', 'estado', 'metodo_pago', 'fecha_creacion')
    list_filter = ('estado', 'metodo_pago', 'fecha_creacion')
    search_fields = ('numero_orden', 'usuario__username', 'usuario__email', 'nombre_envio')
    readonly_fields = ('numero_orden', 'usuario', 'total', 'metodo_pago', 'referencia_pago', 'fecha_creacion', 'fecha_actualizacion')
    inlines = [DetalleOrdenInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_orden', 'usuario', 'estado', 'total')
        }),
        ('Información de Pago', {
            'fields': ('metodo_pago', 'referencia_pago')
        }),
        ('Información de Envío', {
            'fields': ('nombre_envio', 'direccion_envio', 'ciudad_envio', 'estado_envio', 'codigo_postal_envio', 'pais_envio', 'telefono_envio')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )