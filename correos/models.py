from django.db import models

# 1. Modelo de Campañas
class Campana(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la campaña (Uso interno)")
    asunto = models.CharField(max_length=250, verbose_name="Asunto del correo", default="¡Boletín Informativo!")
    contenido = models.TextField(verbose_name="Contenido del mensaje (Texto o HTML)", default="Escribe tu mensaje aquí...")

    class Meta:
        verbose_name = "Campaña"
        verbose_name_plural = "Campañas"

    def __str__(self):
        return self.nombre


# 2. Modelo de Contactos (Limpio y automático)
class EnvioCorreo(models.Model):
    # Usamos un ID autoincremental normal para evitar bloqueos de llaves primarias
    id = models.AutoField(primary_key=True)
    destinatario = models.EmailField(max_length=254, verbose_name="Correo del Destinatario")

    class Meta:
        verbose_name = "Correo Registrado"
        verbose_name_plural = "Lista de Contactos"

    def __str__(self):
        return str(self.destinatario)
