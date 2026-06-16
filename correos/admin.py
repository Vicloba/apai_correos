import json
import urllib.request
import urllib.error
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    # 1. Buscamos la última campaña guardada
    campana = Campana.objects.order_by('-id').first()
    asunto = campana.asunto if campana else "Boletín Informativo"
    contenido = campana.contenido if campana else "<p>Gracias por suscribirte a nuestro boletín.</p>"

    username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
    
    enviados = 0
    fallidos = 0

    # 2. Tu URL de Formspree (Cambia 'mnqeogww' por tu código si ya lo creaste)
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
                    # CORRECCIÓN: Le asignamos el valor "Enviado" para evitar el error de NULL
                    registro.estado = "Enviado"
                    registro.save()
                    enviados += 1
                else:
                    registro.estado = "Fallido"
                    registro.save()
                    fallidos += 1
        except Exception:
            try:
                registro.estado = "Fallido"
                registro.save()
            except:
                pass
            fallidos += 1

    modeladmin.message_user(
        request, 
        f"Campaña procesada. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario', 'estado') # Agregamos estado aquí para verlo en el panel
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')
