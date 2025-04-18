import logging
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Cliente

# Configurar el logger
logger = logging.getLogger('apps.users')

@receiver(post_save, sender=User)
def crear_perfil_cliente(sender, instance, created, **kwargs):
    """
    Signal para crear automáticamente un perfil de Cliente cuando se crea un User.
    """
    if created:
        try:
            Cliente.objects.create(user=instance)
            logger.info(f'Perfil de cliente creado automáticamente para el usuario {instance.username}')
        except Exception as e:
            logger.error(f'Error al crear perfil de cliente para {instance.username}: {str(e)}')

@receiver(post_save, sender=User)
def guardar_perfil_cliente(sender, instance, **kwargs):
    """
    Signal para guardar el perfil de Cliente cuando se actualiza un User.
    """
    try:
        # Solo actualizar si ya existe
        if hasattr(instance, 'cliente'):
            instance.cliente.save()
            logger.debug(f'Perfil de cliente actualizado para el usuario {instance.username}')
    except Cliente.DoesNotExist:
        # Si por alguna razón no existe, crearlo
        Cliente.objects.create(user=instance)
        logger.warning(f'Se creó un perfil de cliente para un usuario existente: {instance.username}')
    except Exception as e:
        logger.error(f'Error al guardar perfil de cliente para {instance.username}: {str(e)}')