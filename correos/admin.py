import base64
import json
import urllib.request
import urllib.error
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'invhbmxvfdtsfyqv')
    
    # 1. Recuperamos la última campaña guardada (asunto y contenido)
    campana = Campana.objects.order_by('-id').first()
    asunto = campana.asunto if campana else "Boletín Informativo"
    contenido = campana.contenido if campana else "<p>Gracias por suscribirte a nuestro boletín.</p>"

    enviados = 0
    fallidos = 0

    # 2. Usamos el endpoint público de la API de Gmail (Puerto Web 443 - Libre en Render)
    url = "https://gmail.googleapis.com/upload/gmail/v1/users/me/messages/send"
    
    # Autenticación básica simulada para la API de Google usando tu contraseña de aplicación
    auth_string = f"{username}:{password}"
    auth_header = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

    for registro in queryset:
        try:
            # Estructuramos el cuerpo del correo en formato crudo MIME
            raw_email = (
                f"From: {username}\r\n"
                f"To: {registro.destinatario}\r\n"
                f"Subject: {asunto}\r\n"
                f"MIME-Version: 1.0\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n\r\n"
                f"{contenido}"
            )
            
            # Codificamos a Base64 seguro para URLs (requisito estricto de Google API)
            raw_bytes = base64.urlsafe_b64encode(raw_email.encode('utf-8'))
            raw_string = raw_bytes.decode('utf-8')
            
            # Formateamos el JSON de petición
            payload = json.dumps({'raw': raw_string}).encode('utf-8')
            
            # Enviamos como POST HTTP (Petición web normal)
            req = urllib.request.Request(url, data=payload, method='POST')
            req.add_header('Authorization', f'Basic {auth_header}')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    enviados += 1
                else:
                    fallidos += 1
        except Exception:
            fallidos += 1

    modeladmin.message_user(
        request, 
        f"Proceso terminado con Gmail API. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')
