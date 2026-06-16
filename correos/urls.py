


from django.urls import path
from correos import views  # <-- Cambiamos "from ." por "from correos" para que Render no se pierda

urlpatterns = [
    # Ruta para el envío masivo usando la base de datos (Postman)
    path('api/enviar-masivo/', views.crear_envio_masivo, name='enviar_masivo'),
    
    # Ruta para el formulario visual de suscripción en el navegador
    path('', views.registrar_suscriptor_formulario, name='formulario_registro'),
    
    # Ruta para generar correos de prueba
    path('api/generar-correos/', views.generar_correos_aleatorios, name='generar_correos'),
]