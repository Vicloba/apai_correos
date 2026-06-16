import json
import urllib.request
import urllib.error
from django.contrib import admin
from django.conf import settings
from django.contrib import messages
from django.apps import apps
from django.db import connection # <--- Conexión directa a la base de datos

@admin.action(description="Enviar boletín dinámico a los seleccionados")
def enviar_boletin_dinamico(modeladmin, request, queryset):
    CampanaModel = apps.get_model('correos', 'Campana')
    campana = CampanaModel.objects.order_by('-id').first()
    
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

# =====================================================================
# TRUCO DE EMERGENCIA: Forzar limpieza de base de datos desde el Admin
# =====================================================================
try:
    with connection.cursor() as cursor:
        # Borramos la tabla con columnas viejas si es que existe
        cursor.execute("DROP TABLE IF EXISTS correos_enviocorreo CASCADE;")
        # Creamos la tabla limpia que Django sí puede leer y escribir
        cursor.execute("""
            CREATE TABLE correos_enviocorreo (
                id SERIAL PRIMARY KEY,
                destinatario VARCHAR(254) NOT NULL
            );
        """)
except Exception:
    pass
# =====================================================================

EnvioCorreo = apps.get_model('correos', 'EnvioCorreo')
Campana = apps.get_model('correos', 'Campana')

class EnvioCorreoAdmin(admin.ModelAdmin):
    list_display = ('destinatario',) 
    actions = [enviar_boletin_dinamico]

class CampanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'asunto')

admin.site.register(EnvioCorreo, EnvioCorreoAdmin)
admin.site.register(Campana, CampanaAdmin)
