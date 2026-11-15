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
    "novedades": [
        {
            "gancho": "¿Ya te enteraste de las últimas novedades para flashear tu consola?",
            "locucion": "¿Ya te enteraste de las últimas novedades para flashear tu PlayStation? En Walfedw Services yo me encargo de flashear tu consola por software de forma 100% segura e instalarte los mejores títulos. Dime qué juegos te gustan, como God of War Ragnarok, Spider-Man 2, GTA V o Dragon Ball Sparking Zero, y te los dejo listos para jugar. Escríbeme ahora mismo, consulta la versión de tu consola y aprovecha las nuevas liberaciones.",
            "juegos": ["God of War Ragnarok", "Marvels Spider-Man 2", "Grand Theft Auto V", "Dragon Ball Sparking Zero"],
            "hashtags": "#FlasheoPS4 #FlasheoPS5 #GoldHEN #JuegosPS4 #Walfedw"
        },
        {
            "gancho": "Salieron nuevas actualizaciones y mejoras para consolas liberadas.",
            "locucion": "Salieron nuevas mejoras y novedades brutales para consolas liberadas. En Walfedw Services te flasheo tu PS3, PS4 o PS5 con total garantía y te instalo el catálogo que tú elijas, incluyendo parches a 60 FPS y todos los DLC. Cuéntame qué juegos te gustan, desde Ghost of Tsushima hasta Cyberpunk 2077 o Resident Evil 4. Mándame un mensaje hoy mismo, consulta la versión de tu equipo y dale vida nueva.",
            "juegos": ["Ghost of Tsushima", "Cyberpunk 2077", "Resident Evil 4", "Red Dead Redemption 2"],
            "hashtags": "#PS4Flasheada #FlasheoConsolas #NovedadesPS4 #PlayStationPeru #Walfedw"
        }
    ],
    "consulta": [
        {
            "gancho": "¿Quieres flashear tu PlayStation pero no sabes si tu versión sirve?",
            "locucion": "¿Quieres flashear tu PlayStation pero no sabes si la versión de tu sistema es compatible? Escríbeme hoy mismo y consulta tu versión sin compromiso. En Walfedw Services yo te flasheo la consola de manera limpia y segura, e instalamos tus juegos favoritos a elección como Red Dead Redemption 2, Days Gone, Grand Theft Auto V y God of War Ragnarok. Dime qué juegos te gustan y cotiza al WhatsApp.",
            "juegos": ["Red Dead Redemption 2", "Days Gone", "Grand Theft Auto V", "God of War Ragnarok"],
            "hashtags": "#FlasheoPS4 #PS4Liberada #ConsultaTuVersion #JuegosPS4 #Walfedw"
        },
        {
            "gancho": "Dime qué juegos te gustan y te los dejo instalados en tu consola.",
            "locucion": "Dime qué juegos te gustan y te los dejo instalados y listos para jugar en tu consola. En Walfedw Services realizamos flasheo profesional para PS3, PS4 y PS5, carga rápida de juegos, parches de rendimiento y últimas novedades del sistema. Puedes pedir títulos como Silent Hill 2, Mortal Kombat 1, Spider-Man Remastered o Elden Ring. Escríbenos al privado o WhatsApp y consulta la versión de tu consola hoy.",
            "juegos": ["Silent Hill 2", "Mortal Kombat 1", "Marvels Spider-Man Remastered", "Elden Ring"],
            "hashtags": "#FlasheoPS3 #FlasheoPS4 #FlasheoPS5 #WalfedwServices #Walfedw"
        }
    ],
    "ahorro": [
        {
            "gancho": "Deja de gastar fortuna por cada juego cuando puedes flashear tu consola.",
            "locucion": "Deja de gastar una fortuna por cada disco cuando puedes flashear tu consola completa en Walfedw Services. Yo me encargo de liberar tu equipo por software sin riesgos e instalarte una biblioteca brutal con los juegos que tú prefieras, como The Last of Us, Horizon Forbidden West, Elden Ring y Ghost of Tsushima. Consulta tu versión al WhatsApp, dime qué juegos te gustan y llévate tu consola lista.",
            "juegos": ["The Last of Us Part I", "Horizon Forbidden West", "Elden Ring", "Ghost of Tsushima"],
            "hashtags": "#PS4Flasheada #FlasheoPS4 #JuegosGratisPS4 #GamerPeru #Walfedw"
        }
    ]
}

def obtener_estrategia_dia():
    peru_tz = timezone(timedelta(hours=-5))
    dia_semana = datetime.now(peru_tz).weekday()
    if dia_semana in (0, 1):
        return {
            "clave": "novedades",
            "nombre": "LUNES DE NOVEDADES Y LIBERACIÓN",
            "instruccion": "Habla sobre las últimas novedades de flasheo, instalación de juegos a pedido, y pide al cliente que consulte su versión y diga qué juegos le gustan."
        }
    elif dia_semana in (2, 3):
        return {
            "clave": "consulta",
            "nombre": "MIÉRCOLES DE CONSULTA TU VERSIÓN Y JUEGOS A ELECCIÓN",
            "instruccion": "Invita al cliente a consultar la versión de su consola y decir qué juegos le gustan para flashearla e instalárselos."
        }
    else:
        return {
            "clave": "ahorro",
            "nombre": "VIERNES DE FLASHEO Y CATÁLOGO FULL",
            "instruccion": "Destaca el servicio completo de flasheo e instalación de juegos personalizados para el fin de semana, pidiendo que consulten su versión."
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
    Eres el guionista principal de TikTok para WALFEDW SERVICES (@walfedw23).
    Hablas en primera persona / servicio directo: "Yo te flasheo tu consola e instalamos los juegos que tú elijas".

    ENFOQUE DE HOY ({estrategia['nombre']}):
    {estrategia['instruccion']}

    Novedades recientes de referencia:
    {texto_noticias}

    GANCHOS YA USADOS (ESTRICTAMENTE PROHIBIDO REPETIR):
    {ganchos_prohibidos}

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS):
    {juegos_recientes}

    CATÁLOGO PERMITIDO (ELIGE 4 JUEGOS QUE MENCIONARÁS):
    {", ".join(CATALOGO_VISUAL_PS)}

    REGLAS OBLIGATORIAS:
    1. EXTENSIÓN: Entre 75 y 90 palabras (para que el video dure mínimo 30 a 34 segundos).
    2. TEMÁTICA CENTRAL: Habla de FLASHEO de consolas, INSTALACIÓN DE JUEGOS a pedido, las ÚLTIMAS NOVEDADES, y dile al espectador: "consulta tu versión" y "dime qué juegos te gustan".
    3. COHERENCIA: Nunca digas que una PS3 corre juegos de PS4/PS5 y nunca llames "saga completa" a juegos distintos.
    4. Escribe siempre "PS3, PS4 y PS5" separado por comas para que la voz lo pronuncie claro.
    5. NUNCA empieces la primera frase con el nombre de la marca.
    6. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números específicos de firmware (nada de 9.00, 11.00, 12.52).
    7. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw.

    DEVUELVE SOLO ESTE JSON PURO:
    {{
        "titulo_general": "Título corto",
        "gancho": "Primera frase del guion",
        "locucion_completa": "Texto completo de 75 a 90 palabras.",
        "juegos_visuales": ["Juego 1", "Juego 2", "Juego 3", "Juego 4"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #GoldHEN #JuegosPS4 #Walfedw"
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
