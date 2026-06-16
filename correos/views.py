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
        
        # CORRECCIÓN: Se agrega 'nombre' que es obligatorio en tu models.py
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
            # NOTA: Tu modelo EnvioCorreo tiene managed=False y solo posee 'destinatario'.
            # Para evitar que Django falle al validar campos inexistentes en el objeto ORM,
            # solo le pasamos el destinatario.
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
        # (El HTML se mantiene exactamente igual a tu archivo original)
        formulario_html = """<!DOCTYPE html>...""" # [Se omite bloque largo por espacio, mantén tu HTML intacto]
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

            ahora = timezone.now()

            with connection.cursor() as cursor:
                # 1. Comprobar duplicados
                cursor.execute('SELECT 1 FROM correos_enviocorreo WHERE destinatario = %s', [correo_usuario])
                existe = cursor.fetchone()
                
                if existe:
                    return JsonResponse({'mensaje': 'Este correo ya estaba registrado en nuestro sistema'}, status=200)

                # 2. Buscar o crear una campaña por defecto usando SQL directo para Render
                cursor.execute('SELECT id FROM correos_campana ORDER BY id DESC LIMIT 1')
                campana_row = cursor.fetchone()
                
                if campana_row:
                    campana_id = campana_row[0]
                else:
                    # CORRECCIÓN SQL: Añadimos la columna 'nombre' que pide tu modelo actual
                    cursor.execute('''
                        INSERT INTO correos_campana (nombre, asunto, contenido) 
                        VALUES (%s, %s, %s) RETURNING id
                    ''', ['Campaña General', 'Campaña General', 'Contenido Inicial'])
                    campana_id = cursor.fetchone()[0]

                # 3. Insertar registro. 
                # NOTA IMPORTANTE: Como tu modelo indica que la tabla es externa o preexistente, 
                # asegúrate de que tu tabla en Postgres realmente tenga las columnas 'estado' y 'campana_id'.
                # Si tu tabla SOLO tiene la columna 'destinatario', remueve los campos sobrantes de este INSERT.
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

    return JsonResponse({'error': 'Método no permitido'}, status=405)