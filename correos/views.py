import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email  
from django.core.exceptions import ValidationError
from django.core.mail import send_mail                 
from django.conf import settings                        
from faker import Faker                                 
from django.db import connection  
from django.utils import timezone  
from .models import Campana, EnvioCorreo

@csrf_exempt
def generar_correos_aleatorios(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body) if request.body else {}
        cantidad = data.get('cantidad', 10)
        fake = Faker()
        
        campana_defecto, _ = Campana.objects.get_or_create(
            nombre="Campaña Automática de Pruebas",
            defaults={
                'asunto': "Campaña de Pruebas Aleatorias", 
                'contenido': 'Contenido generado automáticamente'
            }
        )
        
        correos_falsos = []
        for _ in range(cantidad):
            correo_aleatorio = fake.email() 
            correos_falsos.append(
                EnvioCorreo(destinatario=correo_aleatorio)
            )
        
        EnvioCorreo.objects.bulk_create(correos_falsos)
        
        return JsonResponse({
            'mensaje': f'¡Éxito! Se han creado y guardado {cantidad} correos de prueba en la base de datos.',
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def registrar_suscriptor_formulario(request):
    if request.method == 'GET':
        formulario_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Registro al Boletín</title>
</head>
<body>
    <div style="max-width:400px; margin:50px auto; text-align:center; font-family:sans-serif;">
        <h2>¡Únete a nuestro Boletín!</h2>
        <form method="POST" action="">
            <input type="email" name="correo" placeholder="tu-correo@ejemplo.com" required style="width:100%; padding:10px; margin-bottom:10px;">
            <button type="submit" style="padding:10px 20px; background:#4c51bf; color:white; border:none; width:100%;">Suscribirme</button>
        </form>
    </div>
</body>
</html>"""
        return HttpResponse(formulario_html)

    elif request.method == 'POST':
        try:
            correo_usuario = None
            if request.content_type == 'application/json' or request.body:
                try:
                    data = json.loads(request.body)
                    correo_usuario = data.get('correo')
                except json.JSONDecodeError:
                    correo_usuario = None
            
            if not correo_usuario:
                correo_usuario = request.POST.get('correo')

            if not correo_usuario:
                return JsonResponse({'error': 'El campo "correo" es obligatorio'}, status=400)

            correo_usuario = correo_usuario.strip()
            validate_email(correo_usuario)

            with connection.cursor() as cursor:
                cursor.execute('SELECT 1 FROM correos_enviocorreo WHERE destinatario = %s', [correo_usuario])
                existe = cursor.fetchone()
                
                if existe:
                    return JsonResponse({'mensaje': 'Este correo ya estaba registrado en nuestro sistema'}, status=200)

                cursor.execute('SELECT id FROM correos_campana ORDER BY id DESC LIMIT 1')
                campana_row = cursor.fetchone()
                
                if not campana_row:
                    cursor.execute('''
                        INSERT INTO correos_campana (nombre, asunto, contenido) 
                        VALUES (%s, %s, %s) RETURNING id
                    ''', ['Campaña General', 'Campaña General', 'Contenido Inicial'])

                cursor.execute('''
                    INSERT INTO correos_enviocorreo (destinatario) 
                    VALUES (%s)
                ''', [correo_usuario])

            return JsonResponse({
                'mensaje': '¡Registro exitoso! Correo guardado correctamente',
                'correo_guardado': correo_usuario
            }, status=201)

        except ValidationError:
            return JsonResponse({'error': 'El correo electrónico ingresado no es válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# ==============================================================================
# ¡LA FUNCIÓN QUE LE FALTABA A TU URLS.PY!
# ==============================================================================
@csrf_exempt
def crear_envio_masivo(request):
    """
    Controlador que procesa el envío masivo a través de la API
    enrutada en 'api/enviar-masivo/'
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Utiliza POST.'}, status=405)
        
    try:
        # 1. Obtener la última campaña creada para usar su asunto y contenido
        campana = Campana.objects.order_by('-id').first()
        if not campana:
            return JsonResponse({'error': 'No hay ninguna campaña creada para enviar.'}, status=400)
            
        # 2. Obtener todos los destinatarios de la base de datos
        destinatarios = list(EnvioCorreo.objects.values_list('destinatario', flat=True))
        if not destinatarios:
            return JsonResponse({'error': 'No hay suscriptores en la base de datos.'}, status=400)
            
        enviados = 0
        fallidos = 0
        
        # 3. Enviar el correo uno por uno utilizando la configuración de Gmail
        for correo in destinatarios:
            try:
                send_mail(
                    subject=campana.asunto,
                    message="",  # Se deja vacío porque enviamos HTML
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[correo],
                    html_message=campana.contenido,
                    fail_silently=False
                )
                enviados += 1
            except Exception:
                fallidos += 1
                
        return JsonResponse({
            'mensaje': 'Proceso de envío masivo completado.',
            'campana_utilizada': campana.nombre,
            'total_destinatarios': len(destinatarios),
            'enviados_con_exito': enviados,
            'fallidos': fallidos
        }, status=200)
        
    except Exception as e:
        return JsonResponse({'error': f'Error en el servidor: {str(e)}'}, status=500)