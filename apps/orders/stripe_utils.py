# apps/orders/stripe_utils.py
import logging
import stripe
from django.conf import settings

# Configurar el logger
logger = logging.getLogger('apps.orders.stripe')

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_payment_intent(amount, currency='mxn', metadata=None):
    """
    Crea un PaymentIntent en Stripe.
    
    Args:
        amount: Cantidad en centavos (por ejemplo, $10.00 sería 1000)
        currency: Moneda en formato ISO (por defecto 'mxn' para pesos mexicanos)
        metadata: Diccionario con metadatos adicionales
        
    Returns:
        dict: Información del PaymentIntent creado
    """
    try:
        # Crear el PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convertir a centavos
            currency=currency,
            metadata=metadata or {},
            payment_method_types=['card'],
        )
        
        logger.info(f"PaymentIntent creado: {intent.id}")
        return {
            'client_secret': intent.client_secret,
            'id': intent.id,
            'amount': intent.amount,
            'status': intent.status
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error al crear PaymentIntent: {str(e)}")
        return {
            'error': str(e)
        }

def retrieve_payment_intent(payment_intent_id):
    """
    Recupera la información de un PaymentIntent existente.
    
    Args:
        payment_intent_id: ID del PaymentIntent
        
    Returns:
        dict: Información del PaymentIntent o error
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        logger.info(f"PaymentIntent recuperado: {intent.id}, status: {intent.status}")
        return {
            'id': intent.id,
            'amount': intent.amount,
            'status': intent.status,
            'payment_method': getattr(intent, 'payment_method', None),
            'charges': intent.charges.data if hasattr(intent, 'charges') and intent.charges.data else []
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error al recuperar PaymentIntent: {str(e)}")
        return {
            'error': str(e)
        }

def handle_payment_success(payment_intent_id):
    """
    Maneja la lógica después de un pago exitoso.
    
    Args:
        payment_intent_id: ID del PaymentIntent
        
    Returns:
        bool: True si el pago fue exitoso
    """
    try:
        # Obtenemos el PaymentIntent actualizado
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Verificamos si el pago fue exitoso
        if intent.status == 'succeeded':
            logger.info(f"Pago exitoso para PaymentIntent: {intent.id}")
            return True
        else:
            logger.warning(f"PaymentIntent no completado: {intent.id}, status: {intent.status}")
            return False
    except stripe.error.StripeError as e:
        logger.error(f"Error al manejar pago exitoso: {str(e)}")
        return False