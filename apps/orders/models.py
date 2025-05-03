import logging
import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Producto

# Configurar el logger
logger = logging.getLogger('apps.orders')

class Orden(models.Model):
    """
    Modelo para las órdenes de compra.
    """
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente de pago'),
        ('pagado', 'Pagado'),
        ('preparando', 'Preparando pedido'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    )
    
    METODO_PAGO_CHOICES = (
        ('tarjeta', 'Tarjeta de crédito/débito'),
        ('paypal', 'PayPal'),
    )
    
    # Datos básicos de la orden
    numero_orden = models.CharField(max_length=20, unique=True, editable=False)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordenes')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Datos de pago
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    referencia_pago = models.CharField(max_length=100, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datos de envío
    nombre_envio = models.CharField(max_length=100)
    direccion_envio = models.TextField()
    ciudad_envio = models.CharField(max_length=100)
    estado_envio = models.CharField(max_length=100)
    codigo_postal_envio = models.CharField(max_length=10)
    pais_envio = models.CharField(max_length=100, default='México')
    telefono_envio = models.CharField(max_length=15)
    
    # Datos adicionales
    notas = models.TextField(blank=True, null=True)
    
    recibido = models.BooleanField(default=False, help_text="Indica si el cliente ha confirmado la recepción del pedido")
    fecha_recepcion = models.DateTimeField(null=True, blank=True, help_text="Fecha en que el cliente confirmó la recepción")
    
    def save(self, *args, **kwargs):
        # Generar número de orden único si es nuevo
        if not self.numero_orden:
            self.numero_orden = self.generar_numero_orden()
        super().save(*args, **kwargs)
    
    def generar_numero_orden(self):
        """
        Genera un número de orden único basado en UUID.
        """
        return f"ORD-{uuid.uuid4().hex[:12].upper()}"
    
    def __str__(self):
        return f"Orden #{self.numero_orden}"
    
    
    
    class Meta:
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"
        ordering = ['-fecha_creacion']


class DetalleOrden(models.Model):
    """
    Modelo para los detalles de una orden (productos incluidos).
    """
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    nombre_producto = models.CharField(max_length=200)  # Guardar el nombre en caso de que el producto cambie
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # Precio al momento de la compra
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Calcular el subtotal si no está definido
        if not self.subtotal:
            self.subtotal = self.precio_unitario * self.cantidad
        
        # Guardar el nombre del producto actual
        if not self.nombre_producto:
            self.nombre_producto = self.producto.nombre
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto} en Orden #{self.orden.numero_orden}"
    
    class Meta:
        verbose_name = "Detalle de Orden"
        verbose_name_plural = "Detalles de Órdenes"