import logging
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Configurar el logger
logger = logging.getLogger('apps.users')


class Cliente(models.Model):
    """
    Modelo para almacenar información adicional del cliente más allá del modelo User de Django.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='cliente')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    imagen_perfil = models.ImageField(
        upload_to='usuarios/perfiles/', blank=True, null=True)
    es_administrador = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cliente: {self.user.username}"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-fecha_registro']

# apps/users/models.py (modificar el campo pais en DireccionEnvio)


class DireccionEnvio(models.Model):
    """
    Modelo para almacenar las direcciones de envío de los clientes.
    """
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name='direcciones')
    nombre_completo = models.CharField(max_length=100)
    calle = models.CharField(max_length=100)
    numero_exterior = models.CharField(max_length=10)
    numero_interior = models.CharField(max_length=10, blank=True, null=True)
    colonia = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    # Mantenemos el mismo tamaño de campo
    pais = models.CharField(max_length=100, default='México')
    telefono_contacto = models.CharField(max_length=15)
    es_principal = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.calle} {self.numero_exterior}, {self.colonia}, {self.ciudad}"

    class Meta:
        verbose_name = "Dirección de Envío"
        verbose_name_plural = "Direcciones de Envío"
        ordering = ['-es_principal', '-fecha_actualizacion']


@receiver(post_save, sender=User)
def crear_o_actualizar_cliente(sender, instance, created, **kwargs):
    """
    Signal para crear o actualizar automáticamente un perfil de Cliente cuando se crea o actualiza un User.
    """
    if created:
        Cliente.objects.create(user=instance)
        logger.info(
            f'Nuevo cliente creado para el usuario {instance.username}')
    else:
        # Asegurarse de que el usuario tenga un perfil de cliente
        try:
            instance.cliente.save()
        except Cliente.DoesNotExist:
            Cliente.objects.create(user=instance)
            logger.warning(
                f'Se creó un cliente para un usuario existente: {instance.username}')
