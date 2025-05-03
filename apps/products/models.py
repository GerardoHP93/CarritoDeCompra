import logging
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils import timezone

# Configurar el logger
logger = logging.getLogger('apps.products')

class Categoria(models.Model):
    """
    Modelo para las categorías de productos.
    """
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']


# Añadir en apps/products/models.py
class Proveedor(models.Model):
    """
    Modelo para los proveedores de productos.
    """
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    # Añadir este campo para el tiempo de entrega
    tiempo_entrega_dias = models.PositiveSmallIntegerField(default=5, help_text="Tiempo estimado de entrega en días")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

class Producto(models.Model):
    """
    Modelo para los productos de la tienda.
    """
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    stock = models.PositiveIntegerField(default=0)
    imagen_principal = models.ImageField(upload_to='productos/')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos')
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1
            
            # Verificar si ya existe un producto con ese slug
            while Producto.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            self.slug = slug
            
        super().save(*args, **kwargs)
        
        # Registrar si un producto tiene poco stock o está agotado
        if self.stock <= 5:
            if self.stock == 0:
                logger.warning(f'Producto "{self.nombre}" AGOTADO')
            else:
                logger.warning(f'Producto "{self.nombre}" con stock bajo: {self.stock} unidades')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']
        
    @property
    def esta_agotado(self):
        """
        Propiedad que indica si el producto está agotado.
        """
        return self.stock <= 0


class ImagenProducto(models.Model):
    """
    Modelo para imágenes adicionales de un producto.
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/adicionales/')
    es_principal = models.BooleanField(default=False)
    orden = models.PositiveSmallIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen {self.orden} de {self.producto.nombre}"

    class Meta:
        verbose_name = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Productos"
        ordering = ['producto', 'orden']


class CalificacionProducto(models.Model):
    """
    Modelo para las calificaciones de productos por parte de los clientes.
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='calificaciones')
    cliente = models.ForeignKey('users.Cliente', on_delete=models.CASCADE, related_name='calificaciones')
    puntuacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Calificación de {self.cliente.user.username} para {self.producto.nombre}: {self.puntuacion}/5"

    class Meta:
        verbose_name = "Calificación de Producto"
        verbose_name_plural = "Calificaciones de Productos"
        ordering = ['-fecha_creacion']
        # Asegurar que un usuario solo pueda calificar una vez cada producto
        unique_together = ['producto', 'cliente']
        

# Modificación en apps/products/models.py
import uuid
from django.db import models
from django.utils import timezone

# Actualización en apps/products/models.py

class PedidoProveedor(models.Model):
    """
    Modelo para los pedidos realizados a proveedores para reabastecer el inventario.
    """
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente de pago'),
        ('pagado', 'Pagado'),
        ('en_transito', 'En tránsito'),
        ('recibido', 'Recibido'),
        ('cancelado', 'Cancelado'),
    )
    
    numero_pedido = models.CharField(max_length=20, unique=True, editable=False)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='pedidos')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_estimada_llegada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Generar número de pedido único si es nuevo
        if not self.numero_pedido:
            self.numero_pedido = self._generar_numero_pedido()
            
        # Calcular fecha estimada de llegada si no está definida
        if not self.fecha_estimada_llegada and self.proveedor:
            # Usar el tiempo de entrega específico del proveedor si está disponible
            from datetime import timedelta
            from django.utils import timezone
            tiempo_entrega = getattr(self.proveedor, 'tiempo_entrega_dias', 5)  # Valor predeterminado: 5 días
            self.fecha_estimada_llegada = (timezone.now() + timedelta(days=tiempo_entrega)).date()
            
        super().save(*args, **kwargs)
    
    def _generar_numero_pedido(self):
        """
        Genera un número de pedido único basado en UUID.
        """
        return f"PED-{uuid.uuid4().hex[:8].upper()}"
    
    def __str__(self):
        return f"Pedido #{self.numero_pedido}"
    
    class Meta:
        verbose_name = "Pedido a Proveedor"
        verbose_name_plural = "Pedidos a Proveedores"
        ordering = ['-fecha_solicitud']
        
    # Eliminamos el método marcar_como_recibido ya que no se usa y podría estar causando conflictos
    # La funcionalidad de actualización de stock se maneja directamente en la vista recibir_pedido_proveedor

class DetallePedidoProveedor(models.Model):
    """
    Modelo para los detalles de un pedido a proveedor (productos incluidos).
    """
    pedido = models.ForeignKey(PedidoProveedor, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
def save(self, *args, **kwargs):
    # Generar número de pedido único si es nuevo
    if not self.numero_pedido:
        self.numero_pedido = self.generar_numero_pedido()
        
    # Calcular fecha estimada de llegada si no está definida
    if not self.fecha_estimada_llegada and self.proveedor:
        # Usar el tiempo de entrega específico del proveedor
        from datetime import timedelta
        from django.utils import timezone
        dias_entrega = self.proveedor.tiempo_entrega_dias
        self.fecha_estimada_llegada = (timezone.now() + timedelta(days=dias_entrega)).date()
        
    super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Pedido #{self.pedido.numero_pedido}"
    
    class Meta:
        verbose_name = "Detalle de Pedido a Proveedor"
        verbose_name_plural = "Detalles de Pedidos a Proveedores"