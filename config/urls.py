


from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('correos.urls')),  # Esto le dice: "ve a buscar las rutas dentro de correos"
]