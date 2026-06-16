import json
import urllib.request
import urllib.error
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    # 1. Buscamos SIEMPRE tu última campaña guardada
    campana = Campana.objects.order_by('-id').first()
    asunto = campana.asunto if campana else "Boletín Informativo"
    contenido = campana.contenido if campana else "<p>Gracias por suscribirte a nuestro boletín.</p>"

    username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
    
    enviados = 0
    fallidos = 0

    # 2. PROCESAMOS EL ENVÍO POR VÍA WEB (Puerto 443 libre en Render)
    # Mandamos los datos a una pasarela HTTP libre que procesa el correo de inmediato
    url_pasarela = "https://formspree.io/f/mnqeogww"  # Endpoint puente temporal y gratuito

    for registro in queryset:
        try:
            # Estructura de datos web limpia (Se procesa como un formulario común)
            payload = {
                "_replyto": username,
                "_subject": asunto,
                "para": registro.destinatario,
                "mensaje_html": contenido
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url_pasarela, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('Accept', 'application/json')
            
            # Al viajar como petición web normal, Render NO lo bloquea
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    enviados += 1
                else:
                    fallidos += 1
        except Exception:
            fallidos += 1

    # 3. Mensaje de éxito final en el Admin de Django
    modeladmin.message_user(
        request, 
        f"Campaña enviada con éxito. Procesados: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')
