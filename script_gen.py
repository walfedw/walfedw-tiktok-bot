import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
import requests

HISTORIAL_FILE = "historial.json"

# Catálogo amplio de juegos top de PlayStation para rotar visuales sin repetir
CATALOGO_VISUAL_PS = [
    "God of War Ragnarok",
    "God of War",
    "Marvels Spider-Man Remastered",
    "Marvels Spider-Man Miles Morales",
    "Red Dead Redemption 2",
    "Grand Theft Auto V",
    "Ghost of Tsushima",
    "The Last of Us Part I",
    "Uncharted Legacy of Thieves",
    "Days Gone",
    "Horizon Zero Dawn",
    "Horizon Forbidden West",
    "Cyberpunk 2077",
    "Elden Ring",
    "Resident Evil 4",
    "Silent Hill 2",
    "Dragon Ball Sparking Zero",
    "Mortal Kombat 1",
    "Detroit Become Human"
]

# Banco de guiones variados por categoría (respaldo si la API externa demora)
BANCOS_GUIONES = {
    "ahorro": [
        {
            "gancho": "¿Sigues pagando precios absurdos por cada juego?",
            "locucion": "¿Sigues pagando precios absurdos por cada juego nuevo? Trae tu PS3, PS4 o PS5 a Walfedw Services. Liberamos tu consola y te la entregamos repleta con los mejores títulos listos para jugar. Escríbenos hoy.",
            "juegos": ["God of War Ragnarok", "Marvels Spider-Man Remastered", "Red Dead Redemption 2", "Dragon Ball Sparking Zero"],
            "hashtags": "#FlasheoPS4 #FlasheoPS5 #JuegosPS4 #PlayStationPeru #Walfedw"
        },
        {
            "gancho": "Con lo que cuesta un solo disco llenas toda tu consola.",
            "locucion": "Con lo que cuesta un solo juego en tienda, en Walfedw llenas toda tu consola de estrenos. Servicio de flasheo 100% seguro para PS3, PS4 y PS5 con actualizaciones y DLC incluidos. Cotiza al WhatsApp.",
            "juegos": ["Ghost of Tsushima", "Cyberpunk 2077", "Resident Evil 4", "Grand Theft Auto V"],
            "hashtags": "#PS4Flasheada #FlasheoConsolas #JuegosGratisPS4 #GamerPeru #Walfedw"
        },
        {
            "gancho": "Deja de gastar fortuna en suscripciones mensuales.",
            "locucion": "Deja de gastar una fortuna cada mes para poder jugar. En Walfedw Services liberamos tu PlayStation para que tengas acceso directo a sagas completas sin límites. Mándanos mensaje directo ahora.",
            "juegos": ["The Last of Us Part I", "Uncharted Legacy of Thieves", "Horizon Forbidden West", "Elden Ring"],
            "hashtags": "#PlayStation #PS4Liberada #PS3Hen #FlasheoPS5 #Walfedw"
        }
    ],
    "rendimiento": [
        {
            "gancho": "Tu PS4 esconde potencia a 60 FPS que no estás usando.",
            "locucion": "Tu PS4 esconde potencia a 60 FPS que de fábrica viene bloqueada. En Walfedw liberamos tu sistema, instalamos parches de rendimiento, menús de trucos y catálogo completo. Contáctanos hoy mismo.",
            "juegos": ["Red Dead Redemption 2", "Grand Theft Auto V", "Days Gone", "God of War"],
            "hashtags": "#PS460FPS #ModsPS4 #FlasheoPS4 #ConsolaLiberada #Walfedw"
        },
        {
            "gancho": "Lo que nadie te cuenta de tener una consola liberada.",
            "locucion": "Lo que nadie te cuenta de liberar tu consola en Walfedw: parches de fluidez extrema, emuladores retro, DLC desbloqueados y decenas de juegos instalados al instante. Escríbenos y transforma tu consola.",
            "juegos": ["Silent Hill 2", "Mortal Kombat 1", "Marvels Spider-Man Miles Morales", "Detroit Become Human"],
            "hashtags": "#HomebrewPS4 #FlasheoPS3 #FlasheoPS4 #WalfedwServices #Walfedw"
        },
        {
            "gancho": "Desbloquea el verdadero potencial de tu PlayStation.",
            "locucion": "Desbloquea el verdadero potencial de tu PlayStation con nuestro servicio técnico especializado. Flasheo limpio, sin riesgos, con soporte garantizado y los títulos más pesados ya cargados. Háblanos al WhatsApp.",
            "juegos": ["Dragon Ball Sparking Zero", "Ghost of Tsushima", "Resident Evil 4", "Cyberpunk 2077"],
            "hashtags": "#PS4Flasheada #FlasheoPS5 #JuegosPS4 #PlayStation #Walfedw"
        }
    ],
    "rescate": [
        {
            "gancho": "Si tienes tu PS3 o PS4 juntando polvo, mira esto.",
            "locucion": "Si tienes tu PS3 o PS4 juntando polvo en tu cuarto, dale una segunda vida hoy. En Walfedw Services la liberamos en tiempo récord y la dejamos lista con los mejores éxitos. Escríbenos para cotizar.",
            "juegos": ["God of War Ragnarok", "The Last of Us Part I", "Grand Theft Auto V", "Marvels Spider-Man Remastered"],
            "hashtags": "#PS3 #PS4 #FlasheoPS4 #FlasheoPS3 #Walfedw"
        },
        {
            "gancho": "Convierte tu consola vieja en una máquina definitiva.",
            "locucion": "Convierte tu consola guardada en una máquina definitiva de entretenimiento. Flasheo profesional para PS3, PS4 y PS5, carga rápida de catálogo y respaldo total. Contáctanos al privado o WhatsApp.",
            "juegos": ["Elden Ring", "Horizon Zero Dawn", "Uncharted Legacy of Thieves", "Red Dead Redemption 2"],
            "hashtags": "#ConsolasPeru #FlasheoConsolas #PS4Liberada #Walfedw"
        }
    ]
}

def obtener_estrategia_dia():
    """Define un ángulo comercial distinto según el día de la semana (Hora Perú UTC-5)."""
    peru_tz = timezone(timedelta(hours=-5))
    dia_semana = datetime.now(peru_tz).weekday()  # 0=Lunes, 2=Miércoles, 4=Viernes

    if dia_semana in (0, 1):
        return {
            "clave": "ahorro",
            "nombre": "LUNES DE AHORRO Y CATÁLOGO MASIVO",
            "instruccion": "Enfócate en el AHORRO DE DINERO frente a comprar juegos caros o suscripciones. Destaca que por una fracción del costo se llevan la consola llena de juegos."
        }
    elif dia_semana in (2, 3):
        return {
            "clave": "rendimiento",
            "nombre": "MIÉRCOLES DE 60 FPS, MODS Y POTENCIA OCULTA",
            "instruccion": "Enfócate en VENTAJAS EXCLUSIVAS: parches a 60 FPS, menús de mods/trucos, DLC incluidos y rendimiento al límite en PS3, PS4 y PS5."
        }
    else:
        return {
            "clave": "rescate",
            "nombre": "VIERNES DE RESCATE Y FIN DE SEMANA GAMER",
            "instruccion": "Enfócate en RESCATAR CONSOLAS GUARDADAS sin usar para disfrutar el fin de semana con sagas completas instaladas rápido y 100% seguro."
        }

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Compatibilidad si el historial anterior era una lista simple
                if isinstance(data, list):
                    return {"ganchos": data, "juegos": []}
                if isinstance(data, dict):
                    data.setdefault("ganchos", [])
                    data.setdefault("juegos", [])
                    return data
        except Exception as e:
            print(f"Error leyendo historial: {e}")
    return {"ganchos": [], "juegos": []}

def guardar_historial(gancho, juegos):
    historial = cargar_historial()
    if gancho and gancho not in historial["ganchos"]:
        historial["ganchos"].append(gancho)
    for j in juegos:
        if j and j not in historial["juegos"]:
            historial["juegos"].append(j)

    # Mantener ventana manejable de memoria
    historial["ganchos"] = historial["ganchos"][-40:]
    historial["juegos"] = historial["juegos"][-12:]

    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
        print(f"Memoria actualizada ({len(historial['ganchos'])} guiones únicos registrados).")
    except Exception as e:
        print(f"Error guardando historial: {e}")

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}" for n in noticias[:5]])
    historial = cargar_historial()
    ganchos_prohibidos = "\n".join([f"- {g}" for g in historial["ganchos"][-15:]]) or "Ninguno aún"
    juegos_recientes = ", ".join(historial["juegos"][-8:]) or "Ninguno aún"
    estrategia = obtener_estrategia_dia()

    print(f"Estrategia activa hoy: {estrategia['nombre']}")

    prompt = f"""
    Eres el director creativo y guionista viral de TikTok para WALFEDW SERVICES (@walfedw23).
    Servicios que vendes: Flasheo y liberación 100% segura de PS3, PS4 y PS5, instalación rápida de juegos, parches 60 FPS, DLC y soluciones de sistema.

    ENFOQUE OBLIGATORIO DE HOY ({estrategia['nombre']}):
    {estrategia['instruccion']}

    Novedades de referencia:
    {texto_noticias}

    GANCHOS YA USADOS EN VIDEOS ANTERIORES (ESTRICTAMENTE PROHIBIDO REPETIR O PARECERSE A ESTOS):
    {ganchos_prohibidos}
    - Esa PS4 ahí sentada puede hacer mucho más de lo que crees

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS DISTINTOS DE ESTA LISTA):
    {juegos_recientes}

    CATÁLOGO PERMITIDO PARA ELEGIR 4 JUEGOS VISUALES:
    {", ".join(CATALOGO_VISUAL_PS)}

    REGLAS ESTRICTAS:
    1. Escribe un guion fresco, directo y altamente persuasivo de 35 a 45 palabras (13-16 segundos hablado).
    2. El primer enunciado (gancho) DEBE ser totalmente original y distinto a los videos anteriores.
    3. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de firmware (nada de 9.00, 11.00, 12.52).
    4. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw para liberar su consola.

    DEVUELVE ÚNICAMENTE ESTE JSON PURO:
    {{
        "titulo_general": "Título corto de la campaña de hoy",
        "gancho": "La primera frase exacta del guion",
        "locucion_completa": "Texto completo de 35 a 45 palabras listo para locutar con energía.",
        "juegos_visuales": ["Juego 1 del catálogo", "Juego 2 del catálogo", "Juego 3 del catálogo", "Juego 4 del catálogo"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #JuegosPS4 #PlayStationPeru #Walfedw"
    }}
    """

    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "jsonMode": True
    }

    for intento in range(1, 4):
        try:
            print(f"Intento {intento} solicitando guion novedoso a la IA...")
            response = requests.post(url, json=payload, timeout=45)
            if response.status_code == 200:
                texto = response.text.strip()
                if "```json" in texto:
                    texto = texto.split("```json")[1].split("```")[0].strip()
                elif "```" in texto:
                    texto = texto.split("```")[1].split("```")[0].strip()

                datos = json.loads(texto)
                loc = datos.get("locucion_completa", "").strip()
                gancho = datos.get("gancho", loc.split(".")[0]).strip()
                juegos = datos.get("juegos_visuales", [])

                # Verificar que no sea un gancho repetido ni mencione Switch
                es_repetido = any(gancho.lower()[:25] in prev.lower() for prev in historial["ganchos"])
                tiene_switch = "switch" in loc.lower() or "nintendo" in loc.lower()

                if len(loc.split()) >= 22 and not es_repetido and not tiene_switch:
                    if len(juegos) < 4:
                        disponibles_j = [j for j in CATALOGO_VISUAL_PS if j not in historial["juegos"]]
                        juegos = random.sample(disponibles_j if len(disponibles_j) >= 4 else CATALOGO_VISUAL_PS, 4)
                    datos["juegos_visuales"] = juegos
                    guardar_historial(gancho, juegos)
                    return datos
                else:
                    print("Guion descartado por similitud o filtro. Reintentando...")
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(2)

    # Respaldo inteligente rotativo según el día de la semana
    pool_dia = BANCOS_GUIONES[estrategia["clave"]]
    no_usados = [g for g in pool_dia if g["gancho"] not in historial["ganchos"]]
    if not no_usados:
        todos = [item for sub in BANCOS_GUIONES.values() for item in sub]
        no_usados = [g for g in todos if g["gancho"] not in historial["ganchos"]] or todos

    elegido = random.choice(no_usados)
    guardar_historial(elegido["gancho"], elegido["juegos"])

    return {
        "titulo_general": f"{estrategia['nombre']} - {elegido['gancho'][:30]}",
        "gancho": elegido["gancho"],
        "locucion_completa": elegido["locucion"],
        "juegos_visuales": elegido["juegos"],
        "hashtags": elegido["hashtags"]
    }
