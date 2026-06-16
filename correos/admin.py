from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import EnvioCorreo, Campana

# Registramos las Campañas para que puedas crearlas y editarlas con clics
@admin.register(Campana)
class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')

# Registramos tus contactos de siempre
@admin.register(EnvioCorreo)
class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    actions = ['enviar_boletin_dinamico']

    @admin.action(description="📧 Enviar correo usando la última campaña guardada")
    def enviar_boletin_dinamico(self, request, queryset):
        # El sistema busca de forma automática la última campaña que hiciste con clics
        ultima_campana = Campana.objects.last()
        
        if not ultima_campana:
            self.message_user(request, "❌ Primero debes crear una campaña en la sección de Campañas.", messages.ERROR)
            return

        asunto_usuario = ultima_campana.asunto
        contenido_usuario = ultima_campana.contenido
        
        enviados = 0
        for objeto in queryset:
            correo_limpio = str(objeto).strip()
            if correo_limpio and "@" in correo_limpio:
                try:
                    send_mail(
                        subject=asunto_usuario,
                        message='Abre este correo para ver el contenido completo.',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[correo_limpio],
                        html_message=contenido_usuario, # Tu texto o diseño HTML de la pantalla
                        fail_silently=False,
                    )
                    enviados += 1
                except Exception:
                    pass

        self.message_user(request, f"🎯 ¡Proceso terminado! Correos enviados con éxito: {enviados}.", messages.SUCCESS)
    
