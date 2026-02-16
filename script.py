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

historial_giros = []
giros_totales = 0
TIRO_FUEGO_EVERY = 5 
es_tiro_fuego_actual = False

def render_carrete(rotation_offset):
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    center_y = canvas.height / 2
    angle_step = (2 * math.pi) / len(numeros)
    
    for i in range(len(numeros)):
        angle = (i * angle_step) + rotation_offset
        cos_angle = math.cos(angle)
        
        if cos_angle > -0.3: # Optimización de dibujado
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
        render_carrete(VISUAL_OFFSET)
        girando = False
        finalizar_juego(numeros[target_idx])
        return

    # Ease out quintic para un frenado suave y lujoso
    ease = 1 - math.pow(1 - progress, 5)
    vueltas_totales = 8 * (2 * math.pi)
    distancia_total = vueltas_totales + (target_idx * (2 * math.pi / len(numeros)))
    current_rot = start_rotation - (distancia_total * ease)

    VISUAL_OFFSET = current_rot
    render_carrete(current_rot)
    window.requestAnimationFrame(lambda t: animar(target_idx, duration, start_time, start_rotation))

def actualizar_contador_fuego():
    global giros_totales
    restantes = TIRO_FUEGO_EVERY - (giros_totales % TIRO_FUEGO_EVERY)
    display = document['giros-restantes']
    
    if restantes == 1:
        display.text = "¡AHORA!"
        display.style.color = "#ff4b2b"
    else:
        display.text = str(restantes - 1 if restantes > 1 else 0)
        display.style.color = "#d4af37"

def iniciar_giro(ev=None):
    global puntos, girando, VISUAL_OFFSET, giros_totales, es_tiro_fuego_actual
    if girando: return

    try:
        b_num = int(document['bet-numero'].value or 0)
        b_par = int(document['bet-paridad'].value or 0)
        b_ran = int(document['bet-rango'].value or 0)
        total_apostado = b_num + b_par + b_ran
    except ValueError:
        document['mensaje'].text = "INTRODUCE NÚMEROS VÁLIDOS"
        return

    if total_apostado <= 0:
        document['mensaje'].text = "APUESTA PARA JUGAR"
        return
    if total_apostado > puntos:
        document['mensaje'].text = "TOKENS INSUFICIENTES"
        return

    # Lógica de Tiro de Fuego
    giros_totales += 1
    es_tiro_fuego_actual = (giros_totales % TIRO_FUEGO_EVERY == 0)
    
    puntos -= total_apostado
    girando = True
    document['btn-girar'].disabled = True
    
    if es_tiro_fuego_actual:
        document['main-card'].classList.add('fire-active')
        document['mensaje'].text = "🔥 ¡TIRO DE FUEGO ACTIVADO! 🔥"
        document['mensaje'].classList.add('fire-text')
    else:
        document['mensaje'].text = "GIRANDO..."
        document['mensaje'].classList.remove('fire-text')

    actualizar_ui()
    ganador_idx = random.randint(0, len(numeros) - 1)
    animar(ganador_idx, 4.0, time.time(), VISUAL_OFFSET)

def finalizar_juego(resultado):
    global puntos, es_tiro_fuego_actual
    ganancia_total = 0
    msg_detalle = []
    
    # 1. Pago Número Exacto
    amt_num = int(document['bet-numero'].value or 0)
    if amt_num > 0 and str(resultado) == document['val-numero'].value:
        mult = 100 if es_tiro_fuego_actual else 20
        ganancia_total += amt_num * mult
        msg_detalle.append(f"Número x{mult}")

    # 2. Pago Paridad (0 siempre pierde en paridad/rango)
    if resultado != 0:
        amt_par = int(document['bet-paridad'].value or 0)
        if amt_par > 0:
            val_par = document['val-paridad'].value
            if (val_par == "par" and resultado % 2 == 0) or (val_par == "impar" and resultado % 2 != 0):
                mult = 50 if es_tiro_fuego_actual else 1.9
                ganancia_total += int(amt_par * mult)
                msg_detalle.append(f"Paridad x{mult}")

        amt_ran = int(document['bet-rango'].value or 0)
        if amt_ran > 0:
            val_ran = document['val-rango'].value
            if (val_ran == "bajo" and 1 <= resultado <= 10) or (val_ran == "alto" and 11 <= resultado <= 20):
                mult = 50 if es_tiro_fuego_actual else 1.9
                ganancia_total += int(amt_ran * mult)
                msg_detalle.append(f"Rango x{mult}")

    puntos += ganancia_total
    historial_giros.append(resultado)
    
    # Limpiar efectos visuales
    document['main-card'].classList.remove('fire-active')
    document['btn-girar'].disabled = False

    if ganancia_total > 0:
        document['mensaje'].text = f"¡GANASTE {ganancia_total}! (" + ", ".join(msg_detalle) + ")"
        window.confetti({'particleCount': 150, 'spread': 70, 'origin': {'y': 0.6}})
    else:
        document['mensaje'].text = f"Salió el {resultado}. Suerte la próxima."

    actualizar_ui()
    actualizar_contador_fuego()
    
    if puntos <= 0:
        document['btn-reiniciar'].style.display = "inline-block"
        document['btn-girar'].disabled = True

def actualizar_ui():
    document['puntos'].html = f"{int(puntos):,} <span>TOKENS</span>"

def reiniciar(ev):
    global puntos, giros_totales
    puntos = 1000
    giros_totales = 0
    document['btn-reiniciar'].style.display = "none"
    document['btn-girar'].disabled = False
    document['mensaje'].text = "SISTEMA RECARGADO"
    actualizar_ui()
    actualizar_contador_fuego()

# --- MODAL ---
def abrir_modal(ev):
    document['modal-numeros'].style.display = "flex"
    
    recientes_ul = document['numeros-recientes']
    frios_ul = document['numeros-frios']
    recientes_ul.clear()
    frios_ul.clear()

    if not historial_giros:
        recientes_ul <= html.LI("No hay datos")
        return

    conteo = {i: historial_giros.count(i) for i in range(21)}
    ordenados = sorted(conteo.items(), key=lambda x: x[1], reverse=True)

    for num, cant in ordenados[:5]:
        if cant > 0: recientes_ul <= html.LI(f"{num} ({cant}x)")
    
    for num, cant in ordenados[-5:]:
        frios_ul <= html.LI(f"{num}")

def cerrar_modal(ev):
    document['modal-numeros'].style.display = "none"

# --- INIT ---
for i in range(21):
    document['val-numero'] <= html.OPTION(str(i), value=str(i))

document['btn-girar'].bind('click', iniciar_giro)
document['btn-reiniciar'].bind('click', reiniciar)
document['btn-modal'].bind('click', abrir_modal)
document['close-modal'].bind('click', cerrar_modal)

render_carrete(0)
actualizar_contador_fuego()
timer.set_timeout(lambda: document['loading-screen'].classList.add('loader-hidden'), 1000)