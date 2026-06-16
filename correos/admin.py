import smtplib
from email.mime.text import MIMEText
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'invhbmxvfdtsfyqv')
    
    campana = Campana.objects.order_by('-id').first()
    asunto = campana.asunto if campana else "Boletín Informativo"
    contenido = campana.contenido if campana else "<p>Gracias por suscribirte a nuestro boletín.</p>"

    enviados = 0
    fallidos = 0

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        server.login(username, password)
    except Exception as init_err:
        modeladmin.message_user(
            request, 
            f"Error de conexión con Gmail: {str(init_err)}.", 
            messages.ERROR
        )
        return

    for registro in queryset:
        try:
            message = MIMEText(contenido, "html")
            message['to'] = registro.destinatario
            message['from'] = username
            message['subject'] = asunto
            
            server.sendmail(username, [registro.destinatario], message.as_string())
            enviados += 1
        except Exception:
            fallidos += 1

    try:
        server.quit()
    except:
        pass

    modeladmin.message_user(
        request, 
        f"Proceso de envío terminado. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')
