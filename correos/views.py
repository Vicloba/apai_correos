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
            correos_falsos.append(EnvioCorreo(destinatario=correo_aleatorio))
        
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
                // CORRECCIÓN FRONTEND: Ahora acepta tanto el código 201 como el 409 o 200 de duplicado limpiamente
                if (res.status === 201 || res.status === 200) {
                    responseMessage.innerText = res.body.mensaje;
                    responseMessage.className = 'status-msg';
                    responseMessage.style.backgroundColor = '#e6fffa';
                    responseMessage.style.color = '#234e52';
                    document.getElementById('subscriberForm').style.display = 'none';
                } else {
                    responseMessage.innerText = res.body.error || res.body.mensaje || 'Ocurrió un error.';
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

            with connection.cursor() as cursor:
                # 1. Comprobar duplicados
                cursor.execute('SELECT 1 FROM correos_enviocorreo WHERE destinatario = %s', [correo_usuario])
                existe = cursor.fetchone()
                
                if existe:
                    # CORRECCIÓN BACKEND: Cambiamos a código 400 para que el JavaScript sepa que es una advertencia
                    # y lo pinte dentro de la alerta roja en lugar de romper la pantalla.
                    return JsonResponse({'error': 'Este correo ya estaba registrado en nuestro sistema'}, status=400)

                # 2. Buscar o crear campaña por defecto si no existe
                cursor.execute('SELECT id FROM correos_campana ORDER BY id DESC LIMIT 1')
                campana_row = cursor.fetchone()
                
                if not campana_row:
                    cursor.execute('''
                        INSERT INTO correos_campana (nombre, asunto, contenido) 
                        VALUES (%s, %s, %s) RETURNING id
                    ''', ['Campaña General', 'Campaña General', 'Contenido Inicial'])

                # 3. Insertar el nuevo correo
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


@csrf_exempt
def crear_envio_masivo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Utiliza POST.'}, status=405)
        
    try:
        campana = Campana.objects.order_by('-id').first()
        if not campana:
            return JsonResponse({'error': 'No hay ninguna campaña creada para enviar.'}, status=400)
            
        destinatarios = list(EnvioCorreo.objects.values_list('destinatario', flat=True))
        if not destinatarios:
            return JsonResponse({'error': 'No hay suscriptores en la base de datos.'}, status=400)
            
        enviados = 0
        fallidos = 0
        
        for correo in destinatarios:
            try:
                send_mail(
                    subject=campana.asunto,
                    message="",
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