from django.contrib import admin
from .models import Cliente, DireccionEnvio

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'es_administrador', 'fecha_registro')
    list_filter = ('es_administrador', 'fecha_registro')
    search_fields = ('user__username', 'user__email', 'telefono')
    date_hierarchy = 'fecha_registro'

@admin.register(DireccionEnvio)
class DireccionEnvioAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'nombre_completo', 'ciudad', 'estado', 'es_principal')
    list_filter = ('es_principal', 'ciudad', 'estado')
    search_fields = ('nombre_completo', 'calle', 'colonia', 'ciudad')
    list_select_related = ('cliente', 'cliente__user')