import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
import requests

HISTORIAL_FILE = "historial.json"

# Catálogo de juegos top de PlayStation (incluyendo Astro Bot y exclusivos)
CATALOGO_VISUAL_PS = [
    "Astro Bot",
    "God of War Ragnarok",
    "Marvels Spider-Man 2",
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
    "Days Gone",
    "Uncharted Legacy of Thieves"
]

BANCOS_GUIONES = {
    "ahorro": [
        {
            "gancho": "¿Sigues pagando precios absurdos por cada juego nuevo?",
            "locucion": "¿Sigues pagando precios absurdos por cada juego nuevo? Trae tu PS3, PS4 o PS5 a Walfedw Services. Liberamos tu consola y te la entregamos repleta con joyas como Astro Bot, God of War y Spider-Man. Escríbenos hoy.",
            "juegos": ["Astro Bot", "God of War Ragnarok", "Marvels Spider-Man 2", "Dragon Ball Sparking Zero"],
            "hashtags": "#FlasheoPS4 #FlasheoPS5 #AstroBot #JuegosPS4 #Walfedw"
        },
        {
            "gancho": "Con lo que cuesta un solo disco llenas toda tu consola.",
            "locucion": "Con lo que cuesta un solo juego en tienda, en Walfedw llenas toda tu PlayStation de estrenos. Flasheo 100% seguro para PS3, PS4 y PS5 con juegos, actualizaciones y DLC incluidos. Cotiza al WhatsApp.",
            "juegos": ["Ghost of Tsushima", "Cyberpunk 2077", "Resident Evil 4", "Grand Theft Auto V"],
            "hashtags": "#PS4Flasheada #FlasheoConsolas #PlayStationPeru #GamerPeru #Walfedw"
        }
    ],
    "rendimiento": [
        {
            "gancho": "Tu PS4 esconde potencia a 60 FPS que de fábrica viene bloqueada.",
            "locucion": "Tu PS4 esconde potencia a 60 FPS que de fábrica viene bloqueada. En Walfedw liberamos tu sistema, activamos parches de fluidez, menús de trucos y catálogo completo. Contáctanos hoy mismo.",
            "juegos": ["Red Dead Redemption 2", "Grand Theft Auto V", "Days Gone", "God of War Ragnarok"],
            "hashtags": "#PS460FPS #ModsPS4 #FlasheoPS4 #ConsolaLiberada #Walfedw"
        },
        {
            "gancho": "Desbloquea el verdadero potencial de tu PlayStation hoy.",
            "locucion": "Desbloquea el verdadero potencial de tu PlayStation con nuestro servicio técnico especializado. Flasheo limpio, sin riesgos, con soporte garantizado y los mejores títulos ya instalados. Háblanos al WhatsApp.",
            "juegos": ["Astro Bot", "Silent Hill 2", "Mortal Kombat 1", "Marvels Spider-Man 2"],
            "hashtags": "#PS4Flasheada #FlasheoPS5 #JuegosPS4 #PlayStation #Walfedw"
        }
    ],
    "rescate": [
        {
            "gancho": "Si tienes tu PS3 o PS4 juntando polvo, mira lo que puedes hacer.",
            "locucion": "Si tienes tu PS3 o PS4 juntando polvo en tu cuarto, dale una segunda vida hoy. En Walfedw Services la liberamos en tiempo récord y la dejamos lista con los mejores éxitos. Escríbenos para cotizar.",
            "juegos": ["The Last of Us Part I", "Uncharted Legacy of Thieves", "Elden Ring", "Horizon Forbidden West"],
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
            "instruccion": "Enfócate en el ahorro frente a juegos caros. Menciona títulos top como Astro Bot, God of War o Spider-Man."
        }
    elif dia_semana in (2, 3):
        return {
            "clave": "rendimiento",
            "nombre": "MIÉRCOLES DE 60 FPS, MODS Y POTENCIA OCULTA",
            "instruccion": "Enfócate en parches a 60 FPS, mods, DLC incluidos y rendimiento sin límites en PS3, PS4 y PS5."
        }
    else:
        return {
            "clave": "rescate",
            "nombre": "VIERNES DE RESCATE Y FIN DE SEMANA GAMER",
            "instruccion": "Enfócate en rescatar consolas guardadas para disfrutar el fin de semana con sagas completas."
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
    Eres el guionista viral de TikTok para WALFEDW SERVICES (@walfedw23).
    Servicios: Flasheo y liberación 100% segura de PS3, PS4 y PS5, carga de juegos, parches 60 FPS y DLC.

    ENFOQUE DE HOY ({estrategia['nombre']}):
    {estrategia['instruccion']}

    Tendencias:
    {texto_noticias}

    GANCHOS PROHIBIDOS (NO REPETIR):
    {ganchos_prohibidos}

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS):
    {juegos_recientes}

    CATÁLOGO PERMITIDO (ELIGE 4):
    {", ".join(CATALOGO_VISUAL_PS)}

    REGLAS:
    1. Guion corto, dinámico y persuasivo de 35 a 45 palabras (13-16 segundos hablado).
    2. Primer enunciado (gancho) totalmente nuevo y magnético.
    3. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de versión/firmware.
    4. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw.

    DEVUELVE SOLO ESTE JSON:
    {{
        "titulo_general": "Título corto",
        "gancho": "Primera frase del guion",
        "locucion_completa": "Texto completo de 35 a 45 palabras.",
        "juegos_visuales": ["Juego 1", "Juego 2", "Juego 3", "Juego 4"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #AstroBot #PlayStationPeru #Walfedw"
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

                if len(loc.split()) >= 22 and not es_repetido and not tiene_switch:
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
