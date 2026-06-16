import smtplib
from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

# Si ya tienes otras cosas en tu admin.py, solo asegúrate de actualizar esta función:
@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    # 1. PRUEBA DE CONEXIÓN RÁPIDA (Máximo 5 segundos de espera)
    try:
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        port = getattr(settings, 'EMAIL_PORT', 587)
        
        # Si Gmail no responde en 5 segundos, aborta y no congela el servidor
        server = smtplib.SMTP(host, port, timeout=5)
        server.quit()
    except Exception as smtp_err:
        modeladmin.message_user(
            request, 
            f"Error de conexión con Gmail: No se pudo conectar al servidor de correo. Detalle: {str(smtp_err)}", 
            messages.ERROR
        )
        return

    # 2. ENVIAR LOS CORREOS SI LA CONEXIÓN PASÓ LA PRUEBA
    enviados = 0
    fallidos = 0
    
    for registro in queryset:
        try:
            send_mail(
                subject="Boletín Informativo",
                message="",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[registro.destinatario],
                html_message="<p>Gracias por suscribirte a nuestro boletín dinámico.</p>",
                fail_silently=False
            )
            enviados += 1
        except Exception:
            fallidos += 1

    modeladmin.message_user(
        request, 
        f"Proceso terminado. Enviados con éxito: {enviados}. Fallidos: {fallidos}.", 
        messages.SUCCESS if enviados > 0 else messages.WARNING
    )