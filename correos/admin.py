import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    # Usamos tus credenciales directas de Gmail configuradas en settings
    username = getattr(settings, 'EMAIL_HOST_USER', 'vicky190486@gmail.com')
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', 'invhbmxvfdtsfyqv')
    
    # Buscamos la última campaña guardada para usar su información (asunto y contenido)
    campana = Campana.objects.order_by('-id').first()
    asunto = campana.asunto if campana else "Boletín Informativo"
    contenido = campana.contenido if campana else "<p>Gracias por suscribirte a nuestro boletín.</p>"

    enviados = 0
    fallidos = 0

    # Usamos el puerto alternativo de Google que los servidores no suelen bloquear
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.ehlo()
        server.starttls()  # Cifrado seguro
        server.ehlo()
        server.login(username, password)
    except Exception as e:
        # Si el puerto estándar falla, intentamos una conexión forzada por el puerto SSL directo
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
            server.login(username, password)
        except Exception as init_err:
            modeladmin.message_user(
                request, 
                f"Error de conexión de red con Gmail: {str(init_err)}. Intenta de nuevo en unos minutos.", 
                messages.ERROR
            )
            return

    # Enviamos la campaña a cada uno de los destinatarios seleccionados
    for registro in queryset:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = asunto
            msg['From'] = username
            msg['To'] = registro.destinatario
            
            parte_html = MIMEText(contenido, 'html')
            msg.attach(parte_html)
            
            server.sendmail(username, [registro.destinatario], msg.as_string())
            enviados += 1
        except Exception:
            fallidos += 1

    try:
        server.quit()
    except:
        pass

    modeladmin.message_user(
        request, 
        f"Proceso terminado con Gmail. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )

@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')
