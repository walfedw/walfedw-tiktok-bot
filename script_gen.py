import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
import requests

HISTORIAL_FILE = "historial.json"

CATALOGO_VISUAL_PS = [
    "God of War Ragnarok",
    "Marvels Spider-Man 2",
    "Marvels Spider-Man Remastered",
    "Red Dead Redemption 2",
    "Grand Theft Auto V",
    "Ghost of Tsushima",
    "The Last of Us Part I",
    "Dragon Ball Sparking Zero",
    "Resident Evil 4",
    "Cyberpunk 2077",
    "Elden Ring",
    "Horizon Forbidden West",
    "Mortal Kombat 1",
    "Silent Hill 2",
    "Days Gone"
]

BANCOS_GUIONES = {
    "ahorro": [
        {
            "gancho": "¿Sigues pagando precios absurdos por cada juego nuevo?",
            "locucion": "¿Sigues pagando precios absurdos por cada juego nuevo en tienda? Con lo que gastas en un solo disco, en Walfedw Services liberamos tu consola completa por software y sin riesgos. Desde clásicos legendarios en PS3 hasta los estrenos más pesados en PS4 y PS5, te entregamos tu equipo listo para jugar con joyas como God of War Ragnarok, Spider-Man 2, GTA V y Dragon Ball Sparking Zero. Escríbenos hoy mismo al WhatsApp o Instagram de Walfedw para cotizar.",
            "juegos": ["God of War Ragnarok", "Marvels Spider-Man 2", "Grand Theft Auto V", "Dragon Ball Sparking Zero"],
            "hashtags": "#FlasheoPS4 #FlasheoPS5 #JuegosPS4 #PlayStationPeru #Walfedw"
        },
        {
            "gancho": "Deja de gastar una fortuna cada mes para poder jugar.",
            "locucion": "Deja de gastar una fortuna cada mes en suscripciones y discos caros. En Walfedw Services realizamos flasheo 100% seguro para PS3, PS4 y PS5 con instalación rápida de catálogo, actualizaciones y todos los DLC incluidos. Imagina encender tu consola y tener listos títulos brutales como Ghost of Tsushima, Cyberpunk 2077, Resident Evil 4 y Red Dead Redemption 2 sin restricciones. Mándanos mensaje directo al WhatsApp de Walfedw y libera tu consola hoy.",
            "juegos": ["Ghost of Tsushima", "Cyberpunk 2077", "Resident Evil 4", "Red Dead Redemption 2"],
            "hashtags": "#PS4Flasheada #FlasheoConsolas #GamerPeru #PlayStation #Walfedw"
        }
    ],
    "rendimiento": [
        {
            "gancho": "Tu PS4 esconde potencia a 60 FPS que viene bloqueada.",
            "locucion": "Tu PS4 esconde potencia a 60 FPS que de fábrica viene completamente bloqueada. En Walfedw Services liberamos todo el potencial de tu consola mediante software seguro, activando parches de fluidez extrema, menús de mods exclusivos y acceso directo a decenas de juegos. Disfruta experiencias como Red Dead Redemption 2, Days Gone, Grand Theft Auto V y God of War Ragnarok como nunca antes. Contáctanos al WhatsApp o Instagram de Walfedw para asesoría inmediata.",
            "juegos": ["Red Dead Redemption 2", "Days Gone", "Grand Theft Auto V", "God of War Ragnarok"],
            "hashtags": "#PS460FPS #ModsPS4 #FlasheoPS4 #ConsolaLiberada #Walfedw"
        },
        {
            "gancho": "Todo lo que puedes desbloquear cuando liberas tu PlayStation.",
            "locucion": "Esto es todo lo que ganas cuando liberas tu PlayStation en Walfedw Services: acceso a un catálogo masivo de juegos, parches de rendimiento a 60 FPS, trucos desbloqueados y soporte técnico garantizado para PS3, PS4 y PS5. Preparamos tu sistema en tiempo récord con títulos top como Silent Hill 2, Mortal Kombat 1, Spider-Man Remastered y Elden Ring. Escríbenos al privado o al WhatsApp de Walfedw y transforma tu consola hoy mismo.",
            "juegos": ["Silent Hill 2", "Mortal Kombat 1", "Marvels Spider-Man Remastered", "Elden Ring"],
            "hashtags": "#PS4Flasheada #FlasheoPS5 #JuegosPS4 #WalfedwServices #Walfedw"
        }
    ],
    "rescate": [
        {
            "gancho": "Si tienes tu PS3 o PS4 juntando polvo, mira esto.",
            "locucion": "Si tienes tu PS3 o PS4 juntando polvo en tu cuarto porque los juegos están carísimos, dale una segunda vida hoy mismo. En Walfedw Services liberamos tu consola por software de forma limpia y segura, dejándola repleta con los mejores éxitos listos para disfrutar este fin de semana, incluyendo The Last of Us, Horizon Forbidden West, Elden Ring y Ghost of Tsushima. Escríbenos al WhatsApp de Walfedw y pide tu cotización ahora.",
            "juegos": ["The Last of Us Part I", "Horizon Forbidden West", "Elden Ring", "Ghost of Tsushima"],
            "hashtags": "#PS3 #PS4 #FlasheoPS4 #FlasheoPS3 #Walfedw"
        }
    ]
}

def obtener_estrategia_dia():
    peru_tz = timezone(timedelta(hours=-5))
    dia_semana = datetime.now(peru_tz).weekday()
    if dia_semana in (0, 1):
        return {
            "clave": "ahorro",
            "nombre": "LUNES DE AHORRO Y CATÁLOGO MASIVO",
            "instruccion": "Enfócate en el ahorro de dinero frente a juegos caros y suscripciones. Abre con una pregunta potente sobre lo caro que es comprar juegos."
        }
    elif dia_semana in (2, 3):
        return {
            "clave": "rendimiento",
            "nombre": "MIÉRCOLES DE 60 FPS Y MODS",
            "instruccion": "Enfócate en parches a 60 FPS, mods, trucos y DLC desbloqueados en PS4 y PS5, además de liberación completa para PS3."
        }
    else:
        return {
            "clave": "rescate",
            "nombre": "VIERNES DE RESCATE GAMER",
            "instruccion": "Enfócate en revivir consolas guardadas sin usar para disfrutar el fin de semana con un catálogo completo instalado."
        }

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"ganchos": data, "juegos": []}
                if isinstance(data, dict):
                    data.setdefault("ganchos", [])
                    data.setdefault("juegos", [])
                    return data
        except Exception:
            pass
    return {"ganchos": [], "juegos": []}

def guardar_historial(gancho, juegos):
    historial = cargar_historial()
    if gancho and gancho not in historial["ganchos"]:
        historial["ganchos"].append(gancho)
    for j in juegos:
        if j and j not in historial["juegos"]:
            historial["juegos"].append(j)
    historial["ganchos"] = historial["ganchos"][-40:]
    historial["juegos"] = historial["juegos"][-10:]
    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando historial: {e}")

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}" for n in noticias[:5]])
    historial = cargar_historial()
    ganchos_prohibidos = "\n".join([f"- {g}" for g in historial["ganchos"][-15:]]) or "Ninguno"
    juegos_recientes = ", ".join(historial["juegos"][-6:]) or "Ninguno"
    estrategia = obtener_estrategia_dia()

    prompt = f"""
    Eres un guionista experto en videos virales de TikTok para WALFEDW SERVICES (@walfedw23).
    Servicios: Flasheo y liberación 100% segura por software para PS3, PS4 y PS5, instalación de catálogo de juegos, parches 60 FPS y DLC.

    ENFOQUE DE HOY ({estrategia['nombre']}):
    {estrategia['instruccion']}

    Tendencias de referencia:
    {texto_noticias}

    GANCHOS YA USADOS (ESTRICTAMENTE PROHIBIDO REPETIR):
    {ganchos_prohibidos}

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS):
    {juegos_recientes}

    CATÁLOGO PERMITIDO (ELIGE 4 JUEGOS QUE MENCIONARÁS EN EL GUION):
    {", ".join(CATALOGO_VISUAL_PS)}

    REGLAS ESTRICTAS DE COHERENCIA Y DURACIÓN:
    1. EXTENSIÓN OBLIGATORIA: Escribe entre 75 y 90 palabras (para que el video dure mínimo 30 a 34 segundos hablado con calma).
    2. COHERENCIA TÉCNICA: NUNCA digas que la PS3 corre juegos de PS4/PS5 como Cyberpunk o Elden Ring. Di "Desde clásicos en PS3 hasta los estrenos más pesados en PS4 y PS5".
    3. NUNCA llames "la saga completa" a una mezcla de juegos diferentes; diles "juegazos como..." o "títulos top como...".
    4. Escribe siempre "PS3, PS4 y PS5" separado por comas para que la voz lo lea pausado y claro.
    5. NUNCA empieces con el nombre de la marca. Empieza con un gancho que atrape en 2 segundos.
    6. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de firmware.
    7. Termina con una oración completa invitando a escribir al WhatsApp o Instagram de Walfedw para cotizar.

    DEVUELVE SOLO ESTE JSON PURO:
    {{
        "titulo_general": "Título corto",
        "gancho": "Primera frase del guion",
        "locucion_completa": "Texto completo y coherente de 75 a 90 palabras.",
        "juegos_visuales": ["Juego 1", "Juego 2", "Juego 3", "Juego 4"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #JuegosPS4 #PlayStationPeru #Walfedw"
    }}
    """

    for intento in range(1, 4):
        try:
            response = requests.post(
                "https://text.pollinations.ai/",
                json={"messages": [{"role": "user", "content": prompt}], "jsonMode": True},
                timeout=45
            )
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

                es_repetido = any(gancho.lower()[:25] in prev.lower() for prev in historial["ganchos"])
                tiene_switch = "switch" in loc.lower() or "nintendo" in loc.lower()
                tiene_incoherencia = "saga completa" in loc.lower()

                if len(loc.split()) >= 65 and not es_repetido and not tiene_switch and not tiene_incoherencia:
                    if len(juegos) < 4:
                        juegos = random.sample(CATALOGO_VISUAL_PS, 4)
                    datos["juegos_visuales"] = juegos
                    guardar_historial(gancho, juegos)
                    return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(2)

    pool_dia = BANCOS_GUIONES[estrategia["clave"]]
    elegido = random.choice(pool_dia)
    guardar_historial(elegido["gancho"], elegido["juegos"])
    return {
        "titulo_general": f"{estrategia['nombre']}",
        "gancho": elegido["gancho"],
        "locucion_completa": elegido["locucion"],
        "juegos_visuales": elegido["juegos"],
        "hashtags": elegido["hashtags"]
    }
