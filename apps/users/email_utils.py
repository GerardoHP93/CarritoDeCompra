import logging
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings

# Configurar el logger
logger = logging.getLogger('apps.users')

def enviar_correo(asunto, mensaje, destinatario, html_mensaje=None):
    """
    Función para enviar correos electrónicos.
    
    Args:
        asunto (str): Asunto del correo
        mensaje (str): Mensaje en texto plano
        destinatario (str or list): Correo(s) del destinatario
        html_mensaje (str, optional): Versión HTML del mensaje. Por defecto es None.
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Convertir a lista si es un solo destinatario
        if isinstance(destinatario, str):
            destinatario = [destinatario]
            
        # Enviar correo
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatario,
            html_message=html_mensaje,
            fail_silently=False
        )
        logger.info(f"Correo enviado a {', '.join(destinatario)}")
        return True
    except BadHeaderError:
        logger.error("Cabecera inválida en el correo")
        return False
    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return False