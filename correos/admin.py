import base64
from email.mime.text import MIMEText
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

# Importaciones oficiales de la API de Google
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    # 1. CARGAR CREDENCIALES DE GMAIL MEDIANTE LA API
    try:
        # Usamos tu contraseña de aplicación como Token de acceso directo para la API
        username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
        password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'invhbmxvfdtsfyqv')
        
        # Creamos una conexión simulada pero directa por HTTP (Evita el bloqueo de puertos de Render)
        creds = Credentials(token=None)
        service = build('gmail', 'v1', developerKey=password, static_discovery=False)
    except Exception as init_err:
        modeladmin.message_user(
            request, 
            f"Error inicializando la API de Gmail: {str(init_err)}", 
            messages.ERROR
        )
        return

    enviados = 0
    fallidos = 0
    
    # 2. PROCESAR EL ENVÍO INDIVIDUAL
    for registro in queryset:
        try:
            # Estructuramos el correo de manera nativa en Python
            message = MIMEText("<p>Gracias por suscribirte a nuestro boletín dinámico.</p>", "html")
            message['to'] = registro.destinatario
            message['from'] = username
            message['subject'] = "Boletín Informativo"
            
            # Codificamos el mensaje en el formato Base64 que exige la API de Google
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': raw_message}
            
            # Enviamos el correo usando una petición WEB limpia a través de la API
            # Nota: Al ser una cuenta personal, usamos 'me' o el correo directamente
            service.users().messages().send(userId='me', body=create_message).execute()
            enviados += 1
        except Exception as e:
            fallidos += 1

    modeladmin.message_user(
        request, 
        f"Proceso terminado con Gmail API. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

# REGISTRO DE MODELOS EN EL PANEL
@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')