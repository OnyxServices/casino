from browser import document, window, timer, html
import random
import time
import math

# --- CONFIGURACIÓN ---
puntos = 1000
numeros = list(range(0, 21))
canvas = document["ruleta"]
ctx = canvas.getContext("2d")
RADIUS = 110 
VISUAL_OFFSET = 0
girando = False

def render_carrete(rotation_offset, blur_strength=0):
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    center_y = canvas.height / 2
    for i in range(len(numeros)):
        angle_step = (2 * math.pi) / len(numeros)
        angle = (i * angle_step) + rotation_offset
        cos_angle = math.cos(angle)
        if cos_angle > -0.2:
            y = center_y + RADIUS * math.sin(angle)
            scale = 0.5 + (0.5 * cos_angle)
            opacity = max(0, cos_angle)
            ctx.save()
            ctx.globalAlpha = opacity
            
            num_actual = numeros[i]
            if abs(y - center_y) < 15:
                ctx.fillStyle = "#f1d592"
                ctx.font = f"bold {int(50 * scale)}px Arial Black"
            else:
                ctx.fillStyle = "#ff4b4b" if num_actual == 0 else "white"
                ctx.font = f"bold {int(40 * scale)}px Arial"
            
            ctx.textAlign = "center"
            ctx.textBaseline = "middle"
            ctx.fillText(str(num_actual), canvas.width/2, y)
            ctx.restore()

def animar(target_idx, duration, start_time, start_rotation):
    global VISUAL_OFFSET, girando
    now = time.time()
    elapsed = now - start_time
    progress = elapsed / duration

    if progress >= 1:
        angle_step = (2 * math.pi) / len(numeros)
        VISUAL_OFFSET = -(target_idx * angle_step)
        render_carrete(VISUAL_OFFSET, 0)
        girando = False
        document['btn-girar'].disabled = False
        timer.set_timeout(lambda: finalizar_juego(numeros[target_idx]), 150)
        return

    ease = 1 - math.pow(1 - progress, 5)
    vueltas_totales = 10 * (2 * math.pi)
    distancia_total = vueltas_totales + (target_idx * (2 * math.pi / len(numeros)))
    current_rot = start_rotation - (distancia_total * ease)
    
    VISUAL_OFFSET = current_rot
    render_carrete(current_rot)
    window.requestAnimationFrame(lambda t: animar(target_idx, duration, start_time, start_rotation))

def iniciar_giro(ev=None):
    global puntos, girando, VISUAL_OFFSET
    if girando: return

    try:
        b_num = int(document['bet-numero'].value or 0)
        b_par = int(document['bet-paridad'].value or 0)
        b_ran = int(document['bet-rango'].value or 0)
        total_apostado = b_num + b_par + b_ran
    except:
        document['mensaje'].text = "VALORES NO VÁLIDOS"
        return

    if total_apostado <= 0:
        document['mensaje'].text = "APUESTA ALGO PARA JUGAR"
        return

    if total_apostado > puntos:
        document['mensaje'].text = "SALDO INSUFICIENTE"
        return

    puntos -= total_apostado
    girando = True
    document['btn-girar'].disabled = True
    actualizar_ui()
    
    ganador_idx = random.randint(0, len(numeros) - 1)
    animar(ganador_idx, 3.5, time.time(), VISUAL_OFFSET)

def finalizar_juego(resultado):
    global puntos
    ganancia_total = 0
    msg_detalle = []

    # 1. Check Exacto
    amt_num = int(document['bet-numero'].value or 0)
    if amt_num > 0 and str(resultado) == document['val-numero'].value:
        premio = amt_num * 20
        ganancia_total += premio
        msg_detalle.append(f"Número! (+{premio})")

    # 2. Check Paridad (0 no es par ni impar en este casino)
    amt_par = int(document['bet-paridad'].value or 0)
    if amt_par > 0 and resultado != 0:
        val_par = document['val-paridad'].value
        if (val_par == "par" and resultado % 2 == 0) or (val_par == "impar" and resultado % 2 != 0):
            premio = int(amt_par * 1.9)
            ganancia_total += premio
            msg_detalle.append(f"Paridad! (+{premio})")

    # 3. Check Rango
    amt_ran = int(document['bet-rango'].value or 0)
    if amt_ran > 0 and resultado != 0:
        val_ran = document['val-rango'].value
        if (val_ran == "bajo" and 1 <= resultado <= 10) or (val_ran == "alto" and 11 <= resultado <= 20):
            premio = int(amt_ran * 1.9)
            ganancia_total += premio
            msg_detalle.append(f"Rango! (+{premio})")

    puntos += ganancia_total
    
    if ganancia_total > 0:
        document['mensaje'].text = " / ".join(msg_detalle)
        window.confetti({'particleCount': 100, 'spread': 70, 'origin': {'y': 0.6}})
    else:
        document['mensaje'].text = f"Salió el {resultado}. Suerte la próxima."

    actualizar_ui()
    if puntos <= 0:
        document['btn-reiniciar'].style.display = "block"

def actualizar_ui():
    document['puntos'].html = f"{puntos:,} <span>TOKENS</span>"

def reiniciar(ev):
    global puntos
    puntos = 1000
    document['btn-reiniciar'].style.display = "none"
    document['mensaje'].text = "SISTEMA RECARGADO"
    actualizar_ui()

# Inicialización
for i in range(21):
    document['val-numero'] <= html.OPTION(str(i), value=str(i))

document['btn-girar'].bind('click', iniciar_giro)
document['btn-reiniciar'].bind('click', reiniciar)
render_carrete(0)
actualizar_ui()
timer.set_timeout(lambda: document['loading-screen'].classList.add('loader-hidden'), 500)

from browser import document, window, html

# Abrir modal
def abrir_modal(ev):
    document['modal-numeros'].style.display = "flex"
    actualizar_modal()

# Cerrar modal
def cerrar_modal(ev):
    document['modal-numeros'].style.display = "none"

document['btn-modal'].bind('click', abrir_modal)
document['close-modal'].bind('click', cerrar_modal)

# Actualizar listas del modal
def actualizar_modal():
    # Simulación: últimos 5 números y 5 fríos
    ultimos = [15, 2, 8, 20, 0]  # Aquí pones tu lógica real
    frios = [1, 3, 7, 12, 18]    # Aquí pones tu lógica real

    numeros_recientes = document['numeros-recientes']
    numeros_frios = document['numeros-frios']

    numeros_recientes.clear()
    numeros_frios.clear()

    for n in ultimos:
        numeros_recientes <= html.LI(str(n))

    for n in frios:
        numeros_frios <= html.LI(str(n))