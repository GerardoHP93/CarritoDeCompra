import logging
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Producto

# Configurar el logger
logger = logging.getLogger('apps.cart')

class Carrito(models.Model):
    """
    Modelo para el carrito de compras asociado a un usuario.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carrito')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
        
    @property
    def total(self):
        """
        Calcula el total del carrito sumando el subtotal de cada ítem.
        """
        return sum(item.subtotal for item in self.items.all())
        
    @property
    def cantidad_items(self):
        """
        Retorna la cantidad total de ítems en el carrito.
        """
        return self.items.count()
        
    @property
    def cantidad_productos(self):
        """
        Retorna la cantidad total de productos en el carrito (sumando cantidades).
        """
        return sum(item.cantidad for item in self.items.all())


class ItemCarrito(models.Model):
    """
    Modelo para los items individuales dentro de un carrito.
    """
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en carrito de {self.carrito.usuario.username}"

    class Meta:
        verbose_name = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        # Un producto solo puede estar una vez en el mismo carrito
        unique_together = ['carrito', 'producto']
        ordering = ['-fecha_agregado']
        
    @property
    def subtotal(self):
        """
        Calcula el subtotal del ítem (precio x cantidad).
        """
        return self.producto.precio * self.cantidad