from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.utils import timezone

from .models import Cliente, Producto, Proveedor


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Tu usuario', 'autofocus': True})
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': '••••••••'})


class RegistroForm(forms.ModelForm):
    username = forms.CharField(label='Usuario', max_length=150)
    email = forms.EmailField(label='Correo electrónico', required=False)
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Cliente
        fields = ['identificacion', 'nombre', 'apellidos',
                  'direccion', 'fecha_nacimiento']
        labels = {
            'identificacion': 'Identificación (CC/TI)',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'direccion': 'Dirección',
        }
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = 'form-control'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ese usuario ya está en uso.')
        return username

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        if fecha >= timezone.localdate():
            raise forms.ValidationError('La fecha de nacimiento debe ser anterior a hoy.')
        return fecha

    def clean(self):
        datos = super().clean()
        p1, p2 = datos.get('password1'), datos.get('password2')
        if p1 and p2:
            if p1 != p2:
                self.add_error('password2', 'Las contraseñas no coinciden.')
            else:
                try:
                    password_validation.validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error('password1', e)
        return datos

    def save(self, commit=True):
        User = get_user_model()
        with transaction.atomic():
            usuario = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
            )
            cliente = super().save(commit=False)
            cliente.usuario = usuario
            cliente.save()
        return cliente

class EstiloMixin:
    """Pone clases de Bootstrap a todos los campos."""
    def _estilizar(self):
        for campo in self.fields.values():
            clase = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'
            campo.widget.attrs['class'] = clase


class ClienteForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['identificacion', 'nombre', 'apellidos', 'direccion',
                  'fecha_nacimiento', 'usuario']
        labels = {
            'identificacion': 'Identificación',
            'direccion': 'Dirección',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'usuario': 'Cuenta de acceso (opcional)',
        }
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        if fecha >= timezone.localdate():
            raise forms.ValidationError('La fecha de nacimiento debe ser anterior a hoy.')
        return fecha


class ProveedorForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nit', 'nombre', 'direccion']
        labels = {'nit': 'NIT', 'direccion': 'Dirección'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()
        if not self.instance._state.adding:      # al editar, el NIT (PK) no se cambia
            self.fields['nit'].disabled = True


class ProductoForm(EstiloMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'precio_unitario', 'proveedor']
        labels = {'codigo': 'Código', 'precio_unitario': 'Precio unitario'}
        widgets = {
            'precio_unitario': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estilizar()
        if not self.instance._state.adding:
            self.fields['codigo'].disabled = True