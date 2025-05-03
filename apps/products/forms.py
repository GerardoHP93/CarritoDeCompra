# En apps/products/forms.py (crear este archivo si no existe)
from django import forms
from .models import CalificacionProducto,Proveedor, Producto, PedidoProveedor, DetallePedidoProveedor
from django.forms import inlineformset_factory

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
        
# Modificación en apps/products/forms.py
class PedidoProveedorForm(forms.ModelForm):
    """
    Formulario para crear/editar pedidos a proveedores.
    """
    class Meta:
        model = PedidoProveedor
        fields = ['proveedor', 'notas']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select', 'id': 'id_proveedor'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
class DetallePedidoProveedorForm(forms.ModelForm):
    """
    Formulario para detalles de un pedido a proveedor.
    """
    class Meta:
        model = DetallePedidoProveedor
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select producto-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialmente limitar a productos activos
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)
        
        # Si ya hay un proveedor seleccionado (en caso de edición), filtrar por ese proveedor
        if self.instance and self.instance.pk and self.instance.pedido and self.instance.pedido.proveedor:
            self.fields['producto'].queryset = Producto.objects.filter(
                proveedor=self.instance.pedido.proveedor,
                activo=True
            )

# Crear un formset para DetallePedidoProveedor
DetallePedidoProveedorFormSet = inlineformset_factory(
    PedidoProveedor, 
    DetallePedidoProveedor,
    form=DetallePedidoProveedorForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)