# En apps/products/forms.py (crear este archivo si no existe)
from django import forms
from .models import CalificacionProducto

class CalificacionProductoForm(forms.ModelForm):
    class Meta:
        model = CalificacionProducto
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.Select(
                choices=[(i, f"{i} estrellas") for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }