import json
import urllib.request
import urllib.error
from django.contrib import admin
from django.conf import settings
from django.contrib import messages

# Rompemos el ciclo: quitamos la importación de aquí arriba y la metemos abajo

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    # Importación diferida (dentro de la función)
    from .models import Campana
    
    campana = Campana.objects.order_by('-id').first()
    asunto = campana.asunto if campana else "Boletín Informativo"
    contenido = campana.contenido if campana else "<p>Gracias por suscribirte a nuestro boletín.</p>"

    username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
    
    enviados = 0
    fallidos = 0
    url_pasarela = "https://formspree.io/f/mnqeogww" 

    for registro in queryset:
        try:
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
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    enviados += 1
                else:
                    fallidos += 1
        except Exception:
            fallidos += 1

    modeladmin.message_user(
        request, 
        f"Campaña procesada. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

# Para registrar los modelos sin activar la importación circular arriba:
from .models import EnvioCorreo, Campana

@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')
