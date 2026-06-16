import json
import random
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email  
from django.core.exceptions import ValidationError
from django.core.mail import send_mail                 
from django.conf import settings                        
from faker import Faker                                 
from django.db import connection  # Para comunicarnos directo con la base de datos
from django.utils import timezone  # Para rellenar el campo actualizado_en
from .models import Campana, EnvioCorreo


import smtplib  # <--  Para controlar que Gmail no congele el servidor

@csrf_exempt
def crear_envio_masivo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Debe ser POST'}, status=405)
        
    try:
        data = json.loads(request.body)
        asunto = data.get('asunto')
        contenido = data.get('contenido')

        if not asunto or not contenido:
            return JsonResponse({'error': 'Faltan campos obligatorios (asunto o contenido)'}, status=400)

        # 1. Traer destinatarios con SQL Nativo
        destinatarios_reales = []
        with connection.cursor() as cursor:
            cursor.execute('SELECT DISTINCT destinatario FROM correos_enviocorreo')
            rows = cursor.fetchall()
            destinatarios_reales = [row[0] for row in rows]

        if not destinatarios_reales:
            return JsonResponse({'error': 'No hay ningún correo registrado en la base de datos.'}, status=400)

        # 2. PROBAR CONEXIÓN RÁPIDA CON GMAIL (Máximo 5 segundos de espera)
        try:
            # Revisa qué puerto usas. Cambiamos a una conexión con timeout estricto
            host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            port = getattr(settings, 'EMAIL_PORT', 587)
            
            # Intentamos conectar rápido para ver si el servidor de Render puede hablar con Gmail
            server = smtplib.SMTP(host, port, timeout=5)
            server.quit()
        except Exception as smtp_err:
            return JsonResponse({
                'error': 'No se pudo conectar con los servidores de Gmail.',
                'detalle': str(smtp_err),
                'consejo': 'Verifica el puerto (se recomienda 587) y tus credenciales en las variables de entorno de Render.'
            }, status=500)

        enviados_con_exito = 0
        fallidos = 0

        # 3. ENVIAR CORREOS
        for correo in destinatarios_reales:
            try:
                send_mail(
                    subject=asunto,
                    message='',  
                    from_email=settings.EMAIL_HOST_USER,  
                    recipient_list=[correo],
                    html_message=contenido,  
                    fail_silently=False,
                )
                enviados_con_exito += 1
            except Exception:
                fallidos += 1

        # 4. Intentar guardar campaña en segundo plano
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO correos_campana (asunto, contenido) 
                    VALUES (%s, %s)
                ''', [asunto, contenido])
        except Exception:
            pass

        return JsonResponse({
            'mensaje': 'Envío masivo procesado',
            'enviados_exitosamente': enviados_con_exito,
            'fallidos': fallidos
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)



@csrf_exempt
def generar_correos_aleatorios(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body) if request.body else {}
        cantidad = data.get('cantidad', 10)
        fake = Faker()
        
        correos_falsos = []
        for _ in range(cantidad):
            correo_aleatorio = fake.email() 
            correos_falsos.append(EnvioCorreo(destinatario=correo_aleatorio))
        
        return JsonResponse({
            'mensaje': f'¡Éxito! Se han procesado {cantidad} solicitudes de prueba.',
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro al Boletín</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .card { 
            background: white; 
            padding: 40px 30px; 
            border-radius: 16px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.15); 
            text-align: center; 
            max-width: 400px; 
            width: 100%; 
        }
        h2 { color: #333; margin-top: 0; margin-bottom: 10px; font-size: 26px; }
        p { color: #666; font-size: 15px; margin-bottom: 25px; line-height: 1.5; }
        input[type="email"] { 
            width: 100%; 
            padding: 14px; 
            border: 2px solid #e2e8f0; 
            border-radius: 8px; 
            font-size: 16px; 
            box-sizing: border-box;
            transition: border-color 0.2s;
            margin-bottom: 20px;
        }
        input[type="email"]:focus { outline: none; border-color: #667eea; }
        button { 
            background-color: #4c51bf; 
            color: white; 
            border: none; 
            padding: 14px 20px; 
            font-size: 16px; 
            font-weight: bold;
            border-radius: 8px; 
            cursor: pointer; 
            width: 100%; 
        }
        button:hover { background-color: #434190; }
        .status-msg { display: none; margin-top: 15px; padding: 12px; border-radius: 8px; font-size: 15px; font-weight: 500; }
        .error { background-color: #fed7d7; color: #742a2a; border: 1px solid #feb2b2; }
    </style>
</head>
<body>
    <div class="card" id="formCard">
        <h2>¡Únete a nuestro Boletín!</h2>
        <p>Ingresa tu correo electrónico para recibir las últimas actualizaciones directamente en tu bandeja de entrada.</p>
        <form id="subscriberForm">
            <input type="email" id="emailInput" name="correo" placeholder="tu-correo@ejemplo.com" required>
            <button type="submit" id="submitBtn">Suscribirme</button>
        </form>
        <div id="responseMessage" class="status-msg"></div>
    </div>

    <script>
        document.getElementById('subscriberForm').addEventListener('submit', function(e) {
            e.preventDefault(); 
            const email = document.getElementById('emailInput').value.trim();
            const submitBtn = document.getElementById('submitBtn');
            const responseMessage = document.getElementById('responseMessage');
            
            const regexCorreo = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!regexCorreo.test(email)) {
                responseMessage.style.display = 'block';
                responseMessage.innerText = 'Por favor, ingresa un formato de correo electrónico válido.';
                responseMessage.className = 'status-msg error';
                return;
            }

            submitBtn.innerText = 'Procesando...';
            submitBtn.disabled = true;

            fetch(window.location.href, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ 'correo': email })
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(res => {
                responseMessage.style.display = 'block';
                if (res.status === 201 || res.status === 200) {
                    responseMessage.innerText = res.body.mensaje;
                    responseMessage.className = 'status-msg';
                    responseMessage.style.backgroundColor = '#e6fffa';
                    responseMessage.style.color = '#234e52';
                    document.getElementById('subscriberForm').style.display = 'none';
                } else {
                    responseMessage.innerText = res.body.error || 'Ocurrió un error.';
                    responseMessage.className = 'status-msg error';
                    submitBtn.innerText = 'Intentar de nuevo';
                    submitBtn.disabled = false;
                }
            });
        });
    </script>
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

            ahora = timezone.now()

            with connection.cursor() as cursor:
                # 1. Comprobar duplicados
                cursor.execute('SELECT 1 FROM correos_enviocorreo WHERE destinatario = %s', [correo_usuario])
                existe = cursor.fetchone()
                
                if existe:
                    return JsonResponse({'mensaje': 'Este correo ya estaba registrado en nuestro sistema'}, status=200)

                # 2. Buscar o crear una campaña por defecto para cumplir la restricción de Render
                cursor.execute('SELECT id FROM correos_campana ORDER BY id DESC LIMIT 1')
                campana_row = cursor.fetchone()
                
                if campana_row:
                    campana_id = campana_row[0]
                else:
                    # Si no hay ninguna campaña creada en la base de datos, creamos una rápida
                    cursor.execute('''
                        INSERT INTO correos_campana (asunto, contenido) 
                        VALUES (%s, %s) RETURNING id
                    ''', ['Campaña General', 'Contenido Inicial'])
                    campana_id = cursor.fetchone()[0]

                # 3. Insertar enviando destinatario, estado, actualizado_en y campana_id
                cursor.execute('''
                    INSERT INTO correos_enviocorreo (destinatario, estado, actualizado_en, campana_id) 
                    VALUES (%s, %s, %s, %s)
                ''', [correo_usuario, 'PENDIENTE', ahora, campana_id])

            return JsonResponse({
                'mensaje': '¡Registro exitoso! Correo guardado correctamente',
                'correo_guardado': correo_usuario
            }, status=201)

        except ValidationError:
            return JsonResponse({'error': 'El correo electrónico ingresado no es válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)