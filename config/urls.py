from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from ventas import views as ventas_views
from ventas.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(
        authentication_form=LoginForm,
        redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', ventas_views.registro, name='registro'),
    path('', include('ventas.urls')),
]