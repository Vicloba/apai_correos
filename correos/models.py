from django.db import models

# 1. Aquí agregamos los campos para que puedas escribir el Asunto y Mensaje con clics
class Campana(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la campaña (Uso interno)")
    asunto = models.CharField(max_length=250, verbose_name="Asunto del correo", default="¡Boletín Informativo!")
    contenido = models.TextField(verbose_name="Contenido del mensaje (Texto o HTML)", default="Escribe tu mensaje aquí...")

    def __str__(self):
        return self.nombre


# 🚨 TU MOTOR DE CONTACTOS SE QUEDA EXACTAMENTE IGUAL, INTACTO Y PROTEGIDO:
class EnvioCorreo(models.Model):
    class Meta:
        managed = False
        db_table = 'correos_enviocorreo'

    def __str__(self):
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT * FROM correos_enviocorreo WHERE id = {self.id}')
                fila = cursor.fetchone()
                if fila:
                    for valor in fila:
                        if valor and "@" in str(valor):
                            return str(valor).strip()
        except Exception:
            pass
        return f"Contacto {self.id}"
