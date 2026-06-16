from django.db import models

# 1. Aquí agregamos los campos para que puedas escribir el Asunto y Mensaje con clics
class Campana(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la campaña (Uso interno)")
    asunto = models.CharField(max_length=250, verbose_name="Asunto del correo", default="¡Boletín Informativo!")
    contenido = models.TextField(verbose_name="Contenido del mensaje (Texto o HTML)", default="Escribe tu mensaje aquí...")

    def __str__(self):
        return self.nombre


# MOTOR DE CONTACTOS CORREGIDO: SOLO CORREO, SIN FECHAS NI ENREDOS
class EnvioCorreo(models.Model):
    # Definimos explícitamente que el único campo que nos importa es el correo (destinatario)
    destinatario = models.EmailField(db_column='destinatario', primary_key=True, max_length=254)

    class Meta:
        managed = False  # Protege tu base de datos de Render para no alterarla desde aquí
        db_table = 'correos_enviocorreo'

    def __str__(self):
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Buscamos directamente el correo para mostrarlo limpiamente en tu panel de Django
                cursor.execute(f"SELECT destinatario FROM correos_enviocorreo WHERE destinatario = '{self.destinatario}'")
                fila = cursor.fetchone()
                if fila:
                    return str(fila[0]).strip()
        except Exception:
            pass
        return str(self.destinatario)