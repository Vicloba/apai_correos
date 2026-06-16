from django.db import models

class Campana(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la campaña (Uso interno)")
    asunto = models.CharField(max_length=250, verbose_name="Asunto del correo", default="¡Boletín Informativo!")
    contenido = models.TextField(verbose_name="Contenido del mensaje (Texto o HTML)", default="Escribe tu mensaje aquí...")

    class Meta:
        verbose_name = "Campaña"
        verbose_name_plural = "Campañas"

    def __str__(self):
        return self.nombre

class EnvioCorreo(models.Model):
    destinatario = models.EmailField(db_column='destinatario', primary_key=True, max_length=254)

    class Meta:
        managed = False  
        db_table = 'correos_enviocorreo'
        verbose_name = "Correo Enviado"
        verbose_name_plural = "Envíos de Correos"

    def __str__(self):
        return str(self.destinatario)
