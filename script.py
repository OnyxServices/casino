from browser import document, window, timer, html
import random
import time
import math

# --- CONFIGURACIÓN INICIAL ---
puntos = 1000
intentos = 5
tipo_apuesta = "exacto"
numeros = list(range(0, 21)) # Rango 0-20
canvas = document["ruleta"]
ctx = canvas.getContext("2d")

# Ajuste de radio para que la curvatura se vea bien en el canvas de 220px
RADIUS = 110 
VISUAL_OFFSET = 0
girando = False

# --- VARIABLES DEL TIMER ---
tiempo_restante = 1800 # 30 minutos
timer_interval = None

def render_carrete(rotation_offset, blur_strength=0):
    """ Dibuja los números en el canvas simulando un cilindro 3D """
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    center_y = canvas.height / 2
    
    for i in range(len(numeros)):
        # Calculamos la posición angular de cada número
        angle_step = (2 * math.pi) / len(numeros)
        angle = (i * angle_step) + rotation_offset
        cos_angle = math.cos(angle)
        
        # Solo dibujamos los números en la parte frontal del "cilindro"
        if cos_angle > -0.2:
            y = center_y + RADIUS * math.sin(angle)
            scale = 0.5 + (0.5 * cos_angle)
            opacity = max(0, cos_angle)
            
            ctx.save()
            ctx.globalAlpha = opacity
            
            # Efecto de desenfoque por movimiento si la velocidad es alta
            steps = 1 if blur_strength < 5 else 2
            for s in range(steps):
                offset_blur = (s * blur_strength * 0.1)
                es_ganador = abs(y - center_y) < 15
                
                num_actual = numeros[i]
                if es_ganador:
                    ctx.fillStyle = "#f1d592" # Dorado para el número central
                    ctx.font = f"bold {int(50 * scale)}px Arial Black"
                else:
                    ctx.fillStyle = "#ff4b4b" if num_actual == 0 else "white"
                    ctx.font = f"bold {int(40 * scale)}px Arial"
                
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                ctx.fillText(str(num_actual), canvas.width/2, y + offset_blur)
            ctx.restore()

def animar(target_idx, duration, start_time, start_rotation):
    """ Maneja la animación suavizada (Ease-Out) del giro """
    global VISUAL_OFFSET, girando
    now = time.time()
    elapsed = now - start_time
    progress = elapsed / duration

    if progress >= 1:
        # Finalizar animación exactamente en el número ganador
        angle_step = (2 * math.pi) / len(numeros)
        VISUAL_OFFSET = -(target_idx * angle_step)
        render_carrete(VISUAL_OFFSET, 0)
        girando = False
        document['btn-girar'].disabled = False
        timer.set_timeout(lambda: finalizar_juego(numeros[target_idx]), 150)
        return

    # Curva de frenado (Quintic ease-out)
    ease = 1 - math.pow(1 - progress, 5)
    vueltas_totales = 12 * (2 * math.pi) # 12 vueltas completas antes de frenar
    distancia_total = vueltas_totales + (target_idx * (2 * math.pi / len(numeros)))
    
    current_rot = start_rotation - (distancia_total * ease)
    speed = (1 - progress) * 50 # Para el efecto de desenfoque
    
    VISUAL_OFFSET = current_rot
    render_carrete(current_rot, speed)
    window.requestAnimationFrame(lambda t: animar(target_idx, duration, start_time, start_rotation))

# --- LÓGICA DEL TIMER Y RECARGAS ---
def actualizar_timer():
    global tiempo_restante, intentos, timer_interval, puntos
    if tiempo_restante > 0:
        tiempo_restante -= 1
        mins, secs = tiempo_restante // 60, tiempo_restante % 60
        document['timer-flotante'].text = f"⏳ {mins:02d}:{secs:02d}"
    else:
        timer.clear_interval(timer_interval)
        timer_interval = None
        intentos = 5
        # Si el jugador está totalmente quebrado, le damos un bono de consolación
        if puntos < 10: puntos = 500 
        document['timer-flotante'].style.display = "none"
        document['btn-girar'].style.display = "block"
        document['btn-reiniciar'].style.display = "none"
        document['mensaje'].text = "🔋 SISTEMA RECARGADO"
        actualizar_ui()

def iniciar_timer_si_necesario():
    global timer_interval, tiempo_restante
    if intentos <= 0 and timer_interval is None:
        tiempo_restante = 1800 
        document['timer-flotante'].style.display = "block"
        timer_interval = timer.set_interval(actualizar_timer, 1000)

# --- ACCIONES DE JUEGO ---
def iniciar_giro(ev=None):
    global puntos, intentos, girando, VISUAL_OFFSET
    if girando or intentos <= 0: return
    
    # Validación de seguridad: evitar apuestas vacías, letras o negativos
    try:
        monto = int(document['monto-apuesta'].value)
        if monto <= 0: raise ValueError
    except:
        document['mensaje'].text = "❌ MONTO NO VÁLIDO"
        return
    
    if monto > puntos:
        document['mensaje'].text = "⚠️ SALDO INSUFICIENTE"
        return
    
    # Bloqueo de UI
    intentos -= 1
    puntos -= monto
    girando = True
    document['btn-girar'].disabled = True
    actualizar_ui()
    document['mensaje'].text = "SORTEANDO..."
    
    # Cálculo del ganador
    ganador_idx = random.randint(0, len(numeros) - 1)
    animar(ganador_idx, 4.0, time.time(), VISUAL_OFFSET)

def finalizar_juego(resultado):
    global puntos, intentos
    sub_val = document['sub-opcion'].value
    monto = int(document['monto-apuesta'].value)
    gana = False
    premio = 0

    # Lógica de premios mejorada (x20 para exactos)
    if tipo_apuesta == "exacto":
        if str(resultado) == sub_val:
            premio = int(monto * 20); gana = True
    elif resultado != 0: # El 0 siempre pierde en paridad y rango
        if tipo_apuesta == "paridad":
            if (sub_val == "par" and resultado % 2 == 0) or \
               (sub_val == "impar" and resultado % 2 != 0):
                premio = int(monto * 1.9); gana = True
        elif tipo_apuesta == "rango":
            if (sub_val == "bajo" and 1 <= resultado <= 10) or \
               (sub_val == "alto" and 11 <= resultado <= 20):
                premio = int(monto * 1.9); gana = True

    if gana:
        puntos += premio
        intentos += 1 # Premio extra: recuperas la carga
        document['mensaje'].text = f"💰 ¡GANASTE {premio} TOKENS!"
        # Confetti de victoria
        window.confetti({'particleCount': 100, 'spread': 70, 'origin': {'y': 0.6}})
    else:
        document['mensaje'].text = f"Salió el {resultado}. Suerte la próxima."

    actualizar_ui()
    
    # Verificación de Game Over
    if intentos <= 0:
        if puntos < 10:
            document['btn-girar'].style.display = "none"
            document['btn-reiniciar'].style.display = "block"
            document['mensaje'].text = "CRISIS DE TOKENS"
        else:
            iniciar_timer_si_necesario()
            document['mensaje'].text = "ESPERANDO CARGA AUTOMÁTICA..."

def comprar_carga(ev):
    global puntos, intentos
    if girando: return
    if puntos >= 50:
        puntos -= 50
        intentos += 1
        document['mensaje'].text = "🔋 CARGA ADQUIRIDA"
        actualizar_ui()
    else:
        document['mensaje'].text = "❌ NECESITAS 50 TOKENS"

def actualizar_ui():
    document['puntos'].html = f"{puntos:,} <span>TOKENS</span>"
    document['intentos-display'].text = f"CARGAS: {intentos} / 5"

def cambiar_tipo(ev):
    global tipo_apuesta
    for b in ['bet-exacto', 'bet-paridad', 'bet-rango']:
        document[b].classList.remove('active')
    
    target = ev.target
    target.classList.add('active')
    tipo_apuesta = target.id.split('-')[1]
    
    select = document['sub-opcion']
    select.html = ""
    if tipo_apuesta == "exacto":
        for i in range(0, 21): select <= html.OPTION(str(i), value=str(i))
    elif tipo_apuesta == "paridad":
        select <= html.OPTION("PAR (x1.9)", value="par")
        select <= html.OPTION("IMPAR (x1.9)", value="impar")
    elif tipo_apuesta == "rango":
        select <= html.OPTION("BAJO 1-10 (x1.9)", value="bajo")
        select <= html.OPTION("ALTO 11-20 (x1.9)", value="alto")

def reiniciar(ev):
    global puntos, intentos
    puntos, intentos = 1000, 5
    document['btn-girar'].style.display = "block"
    document['btn-reiniciar'].style.display = "none"
    actualizar_ui()
    document['mensaje'].text = "SISTEMA RESTABLECIDO"

# --- BINDINGS Y CARGA INICIAL ---
document['btn-girar'].bind('click', iniciar_giro)
document['btn-reiniciar'].bind('click', reiniciar)
document['btn-comprar-carga'].bind('click', comprar_carga)
document['bet-exacto'].bind('click', cambiar_tipo)
document['bet-paridad'].bind('click', cambiar_tipo)
document['bet-rango'].bind('click', cambiar_tipo)
document.bind('keydown', lambda ev: iniciar_giro() if ev.keyCode == 13 else None)

# Inicializar interfaz
render_carrete(0)
cambiar_tipo(type('obj', (object,), {'target': document['bet-exacto']}))
actualizar_ui()

# Ocultar pantalla de carga cuando Brython ha terminado de procesar todo
timer.set_timeout(lambda: document['loading-screen'].classList.add('loader-hidden'), 500)