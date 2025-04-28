import logging
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Cliente, DireccionEnvio

# Configurar el logger
logger = logging.getLogger('apps.users')


class UserRegisterForm(UserCreationForm):
    """
    Formulario para el registro de usuarios.
    Extiende UserCreationForm para incluir email.
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar los campos
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar Contraseña'
        })

        # Eliminar textos de ayuda para simplificar el formulario
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean_email(self):
        """
        Validar que el email no esté ya registrado
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Este correo electrónico ya está registrado.")
        return email

    def save(self, commit=True):
        """
        Guardar el nuevo usuario con email
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            try:
                user.save()
                logger.info(f"Usuario {user.username} creado exitosamente")
            except Exception as e:
                logger.error(f"Error al crear usuario: {str(e)}")
                raise
        return user


class UserLoginForm(AuthenticationForm):
    """
    Formulario personalizado para el inicio de sesión
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar campos
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })


class UserUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar información básica del usuario.
    """
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar campos
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_email(self):
        """
        Validar que el email no esté ya registrado (excepto el actual del usuario)
        """
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')

        if User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(
                "Este correo electrónico ya está registrado.")
        return email


class ClienteUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar información adicional del cliente.
    """
    class Meta:
        model = Cliente
        fields = ['telefono', 'fecha_nacimiento', 'imagen_perfil']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_perfil': forms.FileInput(attrs={'class': 'form-control'})
        }

# apps/users/forms.py (modificar el formulario DireccionEnvioForm)


class DireccionEnvioForm(forms.ModelForm):
    """
    Formulario para agregar/editar direcciones de envío.
    """
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

    pais = forms.ChoiceField(label='País', choices=PAISES_CHOICES, initial='México',
                             widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = DireccionEnvio
        exclude = ['cliente', 'fecha_creacion', 'fecha_actualizacion']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_exterior': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_interior': forms.TextInput(attrs={'class': 'form-control'}),
            'colonia': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'es_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
