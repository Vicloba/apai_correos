import json
import random
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email  
from django.core.exceptions import ValidationError
from django.core.mail import send_mail                 
from django.conf import settings                        
from faker import Faker                                 
from .models import Campana, EnvioCorreo

@csrf_exempt
def crear_envio_masivo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Debe ser POST'}, status=405)
        
    try:
        # 1. Leer solo el asunto y contenido desde Postman
        data = json.loads(request.body)
        asunto = data.get('asunto')
        contenido = data.get('contenido')

        if not asunto or not contenido:
            return JsonResponse({'error': 'Faltan campos obligatorios (asunto o contenido)'}, status=400)

        # 2. BUSCAR TODOS LOS CORREOS YA REGISTRADOS EN TU BASE DE DATOS
        todos_los_registros = EnvioCorreo.objects.values_list('destinatario', flat=True).distinct()
        destinatarios_reales = list(todos_los_registros)

        if not destinatarios_reales:
            return JsonResponse({'error': 'No hay ningún correo registrado en la base de datos para enviar.'}, status=400)

        # 3. Guardar la nueva Campaña histórica en PostgreSQL
        campana = Campana.objects.create(asunto=asunto, contenido_html=contenido)

        # 4. Vincular esta campaña con los destinatarios como 'PENDIENTE'
        correos_a_crear = [
            EnvioCorreo(campana=campana, destinatario=correo, estado='PENDIENTE')
            for correo in destinatarios_reales
        ]
        EnvioCorreo.objects.bulk_create(correos_a_crear)
        
        correos_de_la_campana = EnvioCorreo.objects.filter(campana=campana)
        enviados_con_exito = 0
        fallidos = 0

        # 5. Enviar el correo a cada uno usando el servidor de Gmail gratuito
        for objeto_correo in correos_de_la_campana:
            try:
                # 🚀 AQUÍ OCURRE LA MAGIA GRATUITA NATIVA DE DJANGO
                send_mail(
                    subject=asunto,
                    message='',  # Se deja vacío porque enviaremos HTML profesional
                    from_email=settings.EMAIL_HOST_USER,  # Usa tu Gmail configurado
                    recipient_list=[objeto_correo.destinatario],
                    html_message=contenido,  # Aquí se renderiza tu diseño de Postman
                    fail_silently=False,
                )
                
                objeto_correo.estado = 'ENVIADO'
                objeto_correo.save()
                enviados_con_exito += 1

            except Exception as error_envio:
                objeto_correo.estado = 'FALLIDO'
                objeto_correo.error_mensaje = str(error_envio)
                objeto_correo.save()
                fallidos += 1

        # 6. Responder con el reporte total a Postman
        return JsonResponse({
            'mensaje': 'Envío masivo completado exitosamente usando Gmail',
            'total_destinatarios_encontrados': len(destinatarios_reales),
            'campana_id': campana.id,
            'enviados_exitosamente': enviados_con_exito,
            'fallidos': fallidos
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def generar_correos_aleatorios(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body) if request.body else {}
        cantidad = data.get('cantidad', 10)

        fake = Faker()
        
        campana_falsa = Campana.objects.create(
            asunto=f"Campaña de Prueba Aleatoria: {fake.catch_phrase()}",
            contenido_html=f"<p>{fake.text()}</p>"
        )

        correos_falsos = []
        for _ in range(cantidad):
            correo_aleatorio = fake.email() 
            correos_falsos.append(
                EnvioCorreo(
                    campana=campana_falsa, 
                    destinatario=correo_aleatorio, 
                    estado='PENDIENTE'
                )
            )
        
        EnvioCorreo.objects.bulk_create(correos_falsos)

        return JsonResponse({
            'mensaje': f'¡Éxito! Se han creado {cantidad} correos falsos en PostgreSQL',
            'campana_id': campana_falsa.id,
            'ejemplo_de_correo_creado': correos_falsos[0].destinatario
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

            fetch("https://apai-correos.onrender.com/", {
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
            # 1. Intentar leer si viene como JSON puro
            if request.content_type == 'application/json' or request.body:
                try:
                    data = json.loads(request.body)
                    correo_usuario = data.get('correo')
                except json.JSONDecodeError:
                    correo_usuario = None
            
            # 2. Si no se leyó como JSON, intentar leerlo como formulario tradicional
            if not correo_usuario:
                correo_usuario = request.POST.get('correo')

            # 3. Si sigue vacío después de ambos intentos, dar el error
            if not correo_usuario:
                return JsonResponse({'error': 'El campo "correo" es obligatorio'}, status=400)

            correo_usuario = correo_usuario.strip()
            validate_email(correo_usuario)

            campana_autodefecto, creada = Campana.objects.get_or_create(
                asunto="Registro Automático desde Formulario Web",
                defaults={'contenido_html': "<h1>¡Gracias por suscribirte!</h1><p>Pronto recibirás nuestras noticias.</p>"}
            )

            existe = EnvioCorreo.objects.filter(campana=campana_autodefecto, destinatario=correo_usuario).exists()
            if existe:
                return JsonResponse({'mensaje': 'Este correo ya estaba registrado en nuestro sistema'}, status=200)

            nuevo_registro = EnvioCorreo.objects.create(
                campana=campana_autodefecto,
                destinatario=correo_usuario,
                estado='PENDIENTE'
            )

            return JsonResponse({
                'mensaje': '¡Registro exitoso! Guardado en PostgreSQL',
                'registro_id': nuevo_registro.id,
                'correo_guardado': nuevo_registro.destinatario
            }, status=201)

        except ValidationError:
            return JsonResponse({'error': 'El correo electrónico ingresado no es válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

















import resend
import json
import random
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import validate_email  
from django.core.exceptions import ValidationError
from faker import Faker  
from .models import Campana, EnvioCorreo

@csrf_exempt
def crear_envio_masivo(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido. Debe ser POST'}, status=405)
        
    try:
        # 1. Leer solo el asunto y contenido desde Postman
        data = json.loads(request.body)
        asunto = data.get('asunto')
        contenido = data.get('contenido')

        if not asunto or not contenido:
            return JsonResponse({'error': 'Faltan campos obligatorios (asunto o contenido)'}, status=400)

        # 2. 🔍 BUSCAR TODOS LOS CORREOS YA REGISTRADOS EN TU BASE DE DATOS
        todos_los_registros = EnvioCorreo.objects.values_list('destinatario', flat=True).distinct()
        
        # Convertimos en una lista limpia de destinatarios reales
        destinatarios_reales = list(todos_los_registros)

        # Si no hay nadie registrado en la base de datos todavía, avisamos
        if not destinatarios_reales:
            return JsonResponse({'error': 'No hay ningún correo registrado en la base de datos para enviar.'}, status=400)

        # 3. Guardar la nueva Campaña histórica en PostgreSQL
        campana = Campana.objects.create(asunto=asunto, contenido_html=contenido)

        # 4. Vincular esta campaña con los destinatarios como 'PENDIENTE'
        correos_a_crear = [
            EnvioCorreo(campana=campana, destinatario=correo, estado='PENDIENTE')
            for correo in destinatarios_reales
        ]
        EnvioCorreo.objects.bulk_create(correos_a_crear)

        # 5. Configurar la API Key de Resend
        resend.api_key = 're_hwxBb5Rp_5LVnCsU5SwuffYZSBEt8FvFk'
        
        correos_de_la_campana = EnvioCorreo.objects.filter(campana=campana)
        enviados_con_exito = 0
        fallidos = 0

        # 6. Enviar el correo a cada uno usando la API
        for objeto_correo in correos_de_la_campana:
            try:
                params = {
                    "from": "Onboarding <onboarding@resend.dev>",
                    "to": [objeto_correo.destinatario],
                    "subject": asunto,
                    "html": contenido,
                }
                
                resend.Emails.send(params)
                
                objeto_correo.estado = 'ENVIADO'
                objeto_correo.save()
                enviados_con_exito += 1

            except Exception as error_api:
                objeto_correo.estado = 'FALLIDO'
                objeto_correo.error_mensaje = str(error_api)
                objeto_correo.save()
                fallidos += 1

        # 7. Responder con el reporte total de tu base de datos
        return JsonResponse({
            'mensaje': 'Envío masivo completado usando los correos de la base de datos',
            'total_destinatarios_encontrados': len(destinatarios_reales),
            'campana_id': campana.id,
            'enviados_exitosamente': enviados_con_exito,
            'fallidos': fallidos
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def generar_correos_aleatorios(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body) if request.body else {}
        cantidad = data.get('cantidad', 10)

        fake = Faker()
        
        campana_falsa = Campana.objects.create(
            asunto=f"Campaña de Prueba Aleatoria: {fake.catch_phrase()}",
            contenido_html=f"<p>{fake.text()}</p>"
        )

        correos_falsos = []
        for _ in range(cantidad):
            correo_aleatorio = fake.email() 
            correos_falsos.append(
                EnvioCorreo(
                    campana=campana_falsa, 
                    destinatario=correo_aleatorio, 
                    estado='PENDIENTE'
                )
            )
        
        EnvioCorreo.objects.bulk_create(correos_falsos)

        return JsonResponse({
            'mensaje': f'¡Éxito! Se han creado {cantidad} correos falsos en PostgreSQL',
            'campana_id': campana_falsa.id,
            'ejemplo_de_correo_creado': correos_falsos[0].destinatario
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

            fetch("https://apai-correos.onrender.com/", {
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
            # 1. Intentar leer si viene como JSON puro
            if request.content_type == 'application/json' or request.body:
                try:
                    data = json.loads(request.body)
                    correo_usuario = data.get('correo')
                except json.JSONDecodeError:
                    correo_usuario = None
            
            # 2. Si no se leyó como JSON, intentar leerlo como formulario tradicional
            if not correo_usuario:
                correo_usuario = request.POST.get('correo')

            # 3. Si sigue vacío después de ambos intentos, dar el error
            if not correo_usuario:
                return JsonResponse({'error': 'El campo "correo" es obligatorio'}, status=400)

            correo_usuario = correo_usuario.strip()
            validate_email(correo_usuario)

            campana_autodefecto, creada = Campana.objects.get_or_create(
                asunto="Registro Automático desde Formulario Web",
                defaults={'contenido_html': "<h1>¡Gracias por suscribirte!</h1><p>Pronto recibirás nuestras noticias.</p>"}
            )

            existe = EnvioCorreo.objects.filter(campana=campana_autodefecto, destinatario=correo_usuario).exists()
            if existe:
                return JsonResponse({'mensaje': 'Este correo ya estaba registrado en nuestro sistema'}, status=200)

            nuevo_registro = EnvioCorreo.objects.create(
                campana=campana_autodefecto,
                destinatario=correo_usuario,
                estado='PENDIENTE'
            )

            return JsonResponse({
                'mensaje': '¡Registro exitoso! Guardado',
                'registro_id': nuevo_registro.id,
                'correo_guardado': nuevo_registro.destinatario
            }, status=201)

        except ValidationError:
            return JsonResponse({'error': 'El correo electrónico ingresado no es válido.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)



