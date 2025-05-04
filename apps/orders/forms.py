# apps/orders/forms.py
from django import forms
from .models import Orden


class DireccionEnvioForm(forms.Form):
    """
    Formulario para la dirección de envío en el proceso de compra.
    """
    nombre_completo = forms.CharField(label='Nombre completo', max_length=100,
                                      widget=forms.TextInput(attrs={'class': 'form-control'}))
    calle = forms.CharField(label='Calle', max_length=100,
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_exterior = forms.CharField(label='Número exterior', max_length=10,
                                      widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_interior = forms.CharField(label='Número interior (opcional)', max_length=10, required=False,
                                      widget=forms.TextInput(attrs={'class': 'form-control'}))
    colonia = forms.CharField(label='Colonia', max_length=100,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    ciudad = forms.CharField(label='Ciudad', max_length=100,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    estado = forms.CharField(label='Estado', max_length=100,
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    codigo_postal = forms.CharField(label='Código postal', max_length=10,
                                    widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Lista de países principales en orden alfabético
    PAISES_CHOICES = [
        ('', 'Selecciona un país'),
        ('Alemania', 'Alemania'),
        ('Argentina', 'Argentina'),
        ('Australia', 'Australia'),
        ('Brasil', 'Brasil'),
        ('Canadá', 'Canadá'),
        ('Chile', 'Chile'),
        ('China', 'China'),
        ('Colombia', 'Colombia'),
        ('Costa Rica', 'Costa Rica'),
        ('Cuba', 'Cuba'),
        ('Ecuador', 'Ecuador'),
        ('España', 'España'),
        ('Estados Unidos', 'Estados Unidos'),
        ('Francia', 'Francia'),
        ('Guatemala', 'Guatemala'),
        ('Honduras', 'Honduras'),
        ('Italia', 'Italia'),
        ('Japón', 'Japón'),
        ('México', 'México'),
        ('Panamá', 'Panamá'),
        ('Paraguay', 'Paraguay'),
        ('Perú', 'Perú'),
        ('Portugal', 'Portugal'),
        ('Puerto Rico', 'Puerto Rico'),
        ('Reino Unido', 'Reino Unido'),
        ('República Dominicana', 'República Dominicana'),
        ('Rusia', 'Rusia'),
        ('Uruguay', 'Uruguay'),
        ('Venezuela', 'Venezuela'),
    ]

    pais = forms.ChoiceField(label='País', choices=PAISES_CHOICES,
                             initial='México',
                             widget=forms.Select(attrs={'class': 'form-select'}))

    telefono_contacto = forms.CharField(label='Teléfono de contacto', max_length=15,
                                        widget=forms.TextInput(attrs={'class': 'form-control'}))
    usar_direccion_guardada = forms.BooleanField(label='Usar una dirección guardada', required=False,
                                                 widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    direccion_guardada = forms.ChoiceField(label='Seleccionar dirección', required=False,
                                           widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si el usuario tiene direcciones guardadas, agregarlas al select
        if user and user.is_authenticated:
            direcciones = user.cliente.direcciones.all()
            if direcciones:
                self.fields['direccion_guardada'].choices = [
                    (d.id, f"{d.calle} {d.numero_exterior}, {d.colonia}, {d.ciudad}") for d in direcciones]
                self.fields['direccion_guardada'].choices.insert(
                    0, ('', 'Selecciona una dirección'))
            else:
                self.fields['usar_direccion_guardada'].widget = forms.HiddenInput()
                self.fields['direccion_guardada'].widget = forms.HiddenInput()


class MetodoPagoForm(forms.Form):
    """
    Formulario para seleccionar el método de pago.
    """
    METODO_CHOICES = [
        ('', 'Selecciona un método de pago'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
        ('paypal', 'PayPal')
    ]

    metodo_pago = forms.ChoiceField(label='Método de pago', choices=METODO_CHOICES,
                                    widget=forms.Select(attrs={'class': 'form-select'}))

    # Para tarjetas
    numero_tarjeta = forms.CharField(label='Número de tarjeta', max_length=19, required=False,
                                     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000 0000 0000 0000'}))
    titular_tarjeta = forms.CharField(label='Titular de la tarjeta', max_length=100, required=False,
                                      widget=forms.TextInput(attrs={'class': 'form-control'}))
    fecha_expiracion = forms.CharField(label='Fecha de expiración (MM/AA)', max_length=5, required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM/AA'}))
    cvv = forms.CharField(label='CVV', max_length=4, required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123'}))

    TIPO_TARJETA_CHOICES = [
        ('', 'Selecciona tipo de tarjeta'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('amex', 'American Express')
    ]
    tipo_tarjeta = forms.ChoiceField(label='Tipo de tarjeta', choices=TIPO_TARJETA_CHOICES, required=False,
                                     widget=forms.Select(attrs={'class': 'form-select'}))

    def clean(self):
        cleaned_data = super().clean()
        metodo_pago = cleaned_data.get('metodo_pago')

        if metodo_pago == 'tarjeta':
            campos_requeridos = [
                'numero_tarjeta', 'titular_tarjeta', 'fecha_expiracion', 'cvv', 'tipo_tarjeta']
            for campo in campos_requeridos:
                if not cleaned_data.get(campo):
                    self.add_error(campo, 'Este campo es obligatorio.')

        return cleaned_data


class StripePaymentForm(forms.Form):
    """
    Formulario para procesar pagos con Stripe.
    """
    stripe_token = forms.CharField(widget=forms.HiddenInput(), required=False)
    payment_method_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    payment_intent_id = forms.CharField(widget=forms.HiddenInput(), required=False)