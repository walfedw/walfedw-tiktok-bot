import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
import requests

HISTORIAL_FILE = "historial.json"

PALABRAS_BLOQUEADAS_FEED = (
    "do not", "request", "fpkgs", "links", "megathread", "rule", "rules",
    "ban", "mod", "question", "help", "support", "weekly", "daily", "faq",
    "buy", "sell", "switch", "nintendo", "firmware", "9.00", "11.00", "12."
)

BANCOS_POR_FORMATO = {
    "noticiero": [
        {
            "tema": "Última hora: Nuevos parches a 60 FPS para juegazos de PS4",
            "gancho": "Atención gente de PS4, acaban de salir nuevos parches que desbloquean los 60 FPS reales en juegazos pesados.",
            "locucion": "Atención gente de PS4, acaban de salir nuevos parches de comunidad que desbloquean los 60 FPS reales en juegazos pesados. Gracias a estas mejoras, títulos como Red Dead Redemption 2, Bloodborne, Days Gone y God of War Ragnarok se sienten muchísimo más fluidos en tu consola. Si quieres tener tu PS4 o PS3 liberada con estas novedades y tus juegos favoritos ya instalados, escríbeme hoy mismo al WhatsApp de Walfedw y consulta la versión de tu equipo.",
            "juegos": ["Red Dead Redemption 2", "Bloodborne", "Days Gone", "God of War Ragnarok"],
            "hashtags": "#UltimaHoraPS4 #FlasheoPS4 #PS460FPS #JuegosPS4 #Walfedw"
        },
        {
            "tema": "Novedades en mods y actualizaciones de fútbol para PS4 y PS3",
            "gancho": "Si juegas fútbol o mundo abierto en PS4 o PS3, mira la actualización que ya está disponible.",
            "locucion": "Si juegas fútbol o mundo abierto en PS4 o PS3, mira las últimas actualizaciones y mods que ya están disponibles para consolas liberadas. Hoy puedes disfrutar plantillas actualizadas, menús especiales y expansiones completas en títulos como EA SPORTS FC 24, Grand Theft Auto V, Ghost of Tsushima y Dragon Ball Z Kakarot. En Walfedw Services yo me encargo de flashear tu consola por software de manera cien por ciento segura. Consulta tu versión al WhatsApp.",
            "juegos": ["EA SPORTS FC 24", "Grand Theft Auto V", "Ghost of Tsushima", "Dragon Ball Z Kakarot"],
            "hashtags": "#NoticiasPS4 #FlasheoPS4 #FlasheoPS3 #ModsPS4 #Walfedw"
        }
    ],
    "top3": [
        {
            "tema": "Top 3 juegazos de mundo abierto que debes pedir en tu PS4",
            "gancho": "Top 3 juegazos gigantescos que sí o sí debes tener instalados en tu PS4 liberada.",
            "locucion": "Top 3 juegazos gigantescos que sí o sí debes tener instalados en tu PS4 liberada. Número uno: Red Dead Redemption 2, una historia brutal con gráficos increíbles. Número dos: Ghost of Tsushima, combates con katana súper fluidos. Y número tres: Horizon Forbidden West con todas sus expansiones incluidas. En Walfedw Services flasheamos tu PS4 o PS3 y te instalamos el catálogo que tú elijas. Guarda este video, dime qué juegos te gustan y consulta tu versión.",
            "juegos": ["Red Dead Redemption 2", "Ghost of Tsushima", "Horizon Forbidden West", "The Last of Us Part I"],
            "hashtags": "#Top3PS4 #JuegosPS4 #FlasheoPS4 #GamerPeru #Walfedw"
        },
        {
            "tema": "3 cosas ocultas que puedes hacer cuando liberas tu PS4 o PS3",
            "gancho": "Tres funciones brutales que desbloqueas al flashear tu PS4 o PS3 y casi nadie aprovecha.",
            "locucion": "Tres funciones brutales que desbloqueas al flashear tu PS4 o PS3 y casi nadie aprovecha. Primero: instalar decenas de juegos completos con todos sus DLC sin gastar en discos. Segundo: activar parches a 60 FPS y trucos en tus campañas. Y tercero: controlar la temperatura del ventilador para cuidar tu consola al máximo. En Walfedw Services hacemos el proceso limpio y seguro por software. Escríbeme al WhatsApp y consulta tu versión hoy.",
            "juegos": ["Resident Evil 4", "Elden Ring", "Cyberpunk 2077", "Marvels Spider-Man Remastered"],
            "hashtags": "#TrucosPS4 #PS4Flasheada #FlasheoPS4 #FlasheoPS3 #Walfedw"
        }
    ],
    "mitos": [
        {
            "tema": "Mito vs Realidad: ¿Flashear tu PS4 o PS3 malogra la consola?",
            "gancho": "Mito o realidad: ¿flashear tu PS4 o PS3 malogra el lector o recalienta la consola?",
            "locucion": "Mito o realidad: ¿flashear tu PS4 o PS3 malogra el lector o recalienta la consola? Totalmente falso. Cuando se hace por software de manera profesional, tu consola no se abre, conserva su lector intacto y hasta trabaja más fresca controlando el ventilador. Así puedes disfrutar joyas como God of War Ragnarok, Mortal Kombat 11, Sekiro y Grand Theft Auto V sin riesgos. Este fin de semana deja tu consola lista en Walfedw Services, consulta tu versión al WhatsApp.",
            "juegos": ["God of War Ragnarok", "Mortal Kombat 11", "Sekiro Shadows Die Twice", "Grand Theft Auto V"],
            "hashtags": "#MitoVsRealidad #FlasheoPS4 #FlasheoPS3 #PlayStationPeru #Walfedw"
        },
        {
            "tema": "Dudas frecuentes antes de liberar tu PS4 o PS3 este fin de semana",
            "gancho": "Las tres preguntas que más me hacen antes de traer su PS4 o PS3 a flashear.",
            "locucion": "Las tres preguntas que más me hacen antes de traer su PS4 o PS3 a flashear. ¿Se borran mis partidas guardadas? No, tus avances se conservan. ¿Puedo jugar de a dos con mis amigos en casa? Claro que sí, todos los juegos locales funcionan al cien por ciento. Y tercero: ¿yo elijo mis juegos? Tú me dices qué títulos te gustan, como Naruto Storm 4, Resident Evil 4 o Days Gone, y te los dejo listos. Escríbeme hoy.",
            "juegos": ["Naruto Shippuden Ultimate Ninja Storm 4", "Resident Evil 4", "Days Gone", "Bloodborne"],
            "hashtags": "#FlasheoPS4 #PS4Liberada #PreguntasPS4 #JuegosPS4 #Walfedw"
        }
    ]
}

def obtener_formato_dia():
    """Asigna un formato y estilo visual distinto según el día (Lunes, Miércoles o Viernes)."""
    peru_tz = timezone(timedelta(hours=-5))
    dia = datetime.now(peru_tz).weekday()
    if dia in (0, 1):
        return {
            "clave": "noticiero",
            "etiqueta": "🚨 ÚLTIMA HORA • NOVEDADES PS4 Y PS3",
            "instruccion": "FORMATO NOTICIERO GAMER (ÚLTIMA HORA): Abre como una noticia reciente de parches 60 FPS, mods o novedades compatibles con PS4 y PS3, y recién al final invita a instalarlo en Walfedw Services."
        }
    elif dia in (2, 3):
        return {
            "clave": "top3",
            "etiqueta": "🔥 TOP 3 • TRUCOS Y JUEGOS PS4/PS3",
            "instruccion": "FORMATO TOP 3 EDUCATIVO: Presenta una lista numerada ('Número uno... Número dos... Número tres...') de 3 juegos imperdibles o 3 funciones ocultas de una PS4/PS3 liberada para que la gente guarde el video."
        }
    else:
        return {
            "clave": "mitos",
            "etiqueta": "⚡ MITO VS REALIDAD • FINDE GAMER",
            "instruccion": "FORMATO MITO VS REALIDAD / DUDAS FRECUENTES: Responde una duda real de clientes sobre el flasheo de PS4/PS3 (seguridad, partidas, modo 2 jugadores) y cierra invitando a dejar la consola lista para el fin de semana."
        }

def obtener_novedades_limpias(noticias_rss):
    titulares_limpios = []
    for n in (noticias_rss or []):
        t = n.get("titulo", "").strip()
        t_low = t.lower()
        if t and len(t) > 15 and not any(bad in t_low for bad in PALABRAS_BLOQUEADAS_FEED):
            titulares_limpios.append(t)
    return titulares_limpios[:10]

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"temas": data, "ganchos": data, "juegos": []}
                if isinstance(data, dict):
                    data.setdefault("temas", [])
                    data.setdefault("ganchos", [])
                    data.setdefault("juegos", [])
                    return data
        except Exception:
            pass
    return {"temas": [], "ganchos": [], "juegos": []}

def guardar_historial(tema, gancho, juegos):
    historial = cargar_historial()
    if tema and tema not in historial["temas"]:
        historial["temas"].append(tema)
    if gancho and gancho not in historial["ganchos"]:
        historial["ganchos"].append(gancho)
    for j in juegos:
        if j and j not in historial["juegos"]:
            historial["juegos"].append(j)

    historial["temas"] = historial["temas"][-50:]
    historial["ganchos"] = historial["ganchos"][-50:]
    historial["juegos"] = historial["juegos"][-20:]

    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando historial: {e}")

def generar_guion(noticias):
    formato = obtener_formato_dia()
    titulares_rss = obtener_novedades_limpias(noticias)
    bloque_rss = "\n".join([f"- {t}" for t in titulares_rss]) or "- Nuevos parches y catálogos disponibles para PS4 y PS3"

    historial = cargar_historial()
    temas_usados = "\n".join([f"- {t}" for t in historial["temas"][-20:]]) or "Ninguno aún"
    ganchos_usados = "\n".join([f"- {g}" for g in historial["ganchos"][-15:]]) or "Ninguno aún"
    juegos_usados = ", ".join(historial["juegos"][-12:]) or "Ninguno aún"

    prompt = f"""
    Eres el guionista en ESPAÑOL LATINO de TikTok para WALFEDW SERVICES (@walfedw23).
    Hablas en primera persona: "Yo me encargo de flashear tu consola e instalarte los juegos que tú elijas".

    {formato['instruccion']}

    NOTICIAS DE REFERENCIA:
    {bloque_rss}

    TEMAS YA USADOS (PROHIBIDO REPETIR):
    {temas_usados}

    GANCHOS YA USADOS (PROHIBIDO REPETIR):
    {ganchos_usados}

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS DISTINTOS):
    {juegos_usados}

    REGLAS OBLIGATORIAS:
    1. PRIORIDAD CONSOLAS: 80% enfoque en **PS4** y 20% en **PS3**. Menciona **PS5** solo de paso o ni lo menciones.
    2. JUEGOS COMPATIBLES: Elige 4 juegazos reales de **PS4** (o clásicos de **PS3**). PROHIBIDO exclusivos solo de PS5 (nada de Spider-Man 2 ni Black Myth Wukong).
    3. EXTENSIÓN: Entre 75 y 90 palabras (para que el video dure de 30 a 35 segundos).
    4. Escribe siempre "cien por ciento" en letras (NUNCA uses el símbolo %).
    5. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw, consultar la versión de su consola y decir qué juegos le gustan.
    6. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de firmware.

    DEVUELVE SOLO ESTE JSON PURO:
    {{
        "formato_dia": "{formato['clave']}",
        "etiqueta_formato": "{formato['etiqueta']}",
        "tema_novedad": "Resumen corto del tema de hoy",
        "titulo_general": "Título del video",
        "gancho": "Primera frase del guion",
        "locucion_completa": "Texto completo en español fluido de 75 a 90 palabras.",
        "juegos_visuales": ["Juego PS4 1", "Juego PS4 2", "Juego PS4 3", "Juego PS4 4"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #FlasheoPS3 #JuegosPS4 #Walfedw"
    }}
    """

    for intento in range(1, 4):
        try:
            print(f"Intento {intento}: generando guion formato [{formato['clave'].upper()}]...")
            response = requests.post(
                "https://text.pollinations.ai/",
                json={"messages": [{"role": "user", "content": prompt}], "jsonMode": True},
                timeout=35
            )
            if response.status_code == 200:
                texto = response.text.strip()
                if "```json" in texto:
                    texto = texto.split("```json")[1].split("```")[0].strip()
                elif "```" in texto:
                    texto = texto.split("```")[1].split("```")[0].strip()

                datos = json.loads(texto)
                loc = datos.get("locucion_completa", "").replace("%", " por ciento").strip()
                gancho = datos.get("gancho", loc.split(".")[0]).strip()
                tema = datos.get("tema_novedad", gancho[:40]).strip()
                juegos = datos.get("juegos_visuales", [])

                es_repetido = any(gancho.lower()[:25] in prev.lower() for prev in historial["ganchos"])
                tiene_bloqueadas = any(b in loc.lower() for b in ("do not", "fpkgs", "switch", "nintendo", "spider-man 2", "wukong"))

                if len(loc.split()) >= 65 and not es_repetido and not tiene_bloqueadas and len(juegos) >= 3:
                    datos["locucion_completa"] = loc
                    datos["formato_dia"] = formato["clave"]
                    datos["etiqueta_formato"] = formato["etiqueta"]
                    guardar_historial(tema, gancho, juegos)
                    print(f"Guion IA aprobado [{formato['clave']}]: {tema}")
                    return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(1)

    pool = BANCOS_POR_FORMATO[formato["clave"]]
    disponibles = [c for c in pool if c["tema"] not in historial["temas"]] or pool
    elegido = random.choice(disponibles)

    guardar_historial(elegido["tema"], elegido["gancho"], elegido["juegos"])
    return {
        "formato_dia": formato["clave"],
        "etiqueta_formato": formato["etiqueta"],
        "tema_novedad": elegido["tema"],
        "titulo_general": elegido["tema"],
        "gancho": elegido["gancho"],
        "locucion_completa": elegido["locucion"],
        "juegos_visuales": elegido["juegos"],
        "hashtags": elegido["hashtags"]
    }
