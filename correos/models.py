from django.db import models

# 1. Modelo de Campañas (Para escribir Asunto y Mensaje desde el panel de Django)
class Campana(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la campaña (Uso interno)")
    asunto = models.CharField(max_length=250, verbose_name="Asunto del correo", default="¡Boletín Informativo!")
    contenido = models.TextField(verbose_name="Contenido del mensaje (Texto o HTML)", default="Escribe tu mensaje aquí...")

    class Meta:
        verbose_name = "Campaña"
        verbose_name_plural = "Campañas"

    def __str__(self):
        return self.nombre


# 2. MOTOR DE CONTACTOS OPTIMIZADO (Seguro para Render y rápido)
class EnvioCorreo(models.Model):
    # Definimos la llave primaria apuntando a la columna 'destinatario'
    destinatario = models.EmailField(db_column='destinatario', primary_key=True, max_length=254)

    class Meta:
        managed = False  # Protege tu base de datos de Render para no alterarla desde aquí
        db_table = 'correos_enviocorreo'
        verbose_name = "Correo Enviado"
        verbose_name_plural = "Envíos de Correos"

    # CORRECCIÓN CRÍTICA: Eliminamos la consulta SQL cruda interna.
    # Ahora Django mostrará el correo instantáneamente desde la memoria sin saturar a Render.
    def __str__(self):
        return str(self.destinatario)