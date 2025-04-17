import logging
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

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