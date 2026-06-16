

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('correos.urls')),  # Enruta la raíz a las URLs de tu aplicación
]