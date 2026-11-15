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

NOVEDADES_CURADAS_SPANISH = [
    {
        "tema": "Lanzamiento de Black Myth Wukong y joyas de acción",
        "gancho": "¿Ya viste el nivel gráfico de los últimos estrenos que están rompiendo PlayStation?",
        "detalle": "títulos de nueva generación como Black Myth Wukong y Tekken 8",
        "juegos": ["Black Myth Wukong", "Tekken 8", "God of War Ragnarok", "Ghost of Tsushima"]
    },
    {
        "tema": "Parches a 60 FPS en clásicos de PS4",
        "gancho": "¿Sabías que puedes correr juegos pesados de PS4 a 60 FPS reales en tu consola?",
        "detalle": "los nuevos parches de desbloqueo de cuadros por segundo en mundos abiertos",
        "juegos": ["Red Dead Redemption 2", "Bloodborne", "Days Gone", "Grand Theft Auto V"]
    },
    {
        "tema": "Remakes de terror y supervivencia en PlayStation",
        "gancho": "Los remakes de terror más esperados ya están disponibles para disfrutar sin límites.",
        "detalle": "el regreso de clásicos brutales como Silent Hill 2 y Resident Evil 4",
        "juegos": ["Silent Hill 2", "Resident Evil 4", "The Last of Us Part I", "Cyberpunk 2077"]
    },
    {
        "tema": "Nuevos juegos de pelea y anime en consola",
        "gancho": "Si eres fanático de los juegos de pelea y anime, mira lo que puedes tener en tu consola.",
        "detalle": "estrenos explosivos como Dragon Ball Sparking Zero y Mortal Kombat 1",
        "juegos": ["Dragon Ball Sparking Zero", "Mortal Kombat 1", "Marvels Spider-Man 2", "Elden Ring"]
    },
    {
        "tema": "Aventura y mundo abierto en PS4 y PS5",
        "gancho": "¿Sigues pagando precios altísimos por cada juego nuevo en tienda?",
        "detalle": "aventuras gigantescas como Horizon Forbidden West y Spider-Man 2",
        "juegos": ["Horizon Forbidden West", "Marvels Spider-Man 2", "Uncharted Legacy of Thieves", "God of War Ragnarok"]
    }
]

def obtener_novedades_limpias(noticias_rss):
    """Filtra titulares reales en español y descarta avisos o reglas en inglés."""
    titulares_limpios = []
    for n in (noticias_rss or []):
        t = n.get("titulo", "").strip()
        t_low = t.lower()
        if t and len(t) > 15 and not any(bad in t_low for bad in PALABRAS_BLOQUEADAS_FEED):
            titulares_limpios.append(t)
    return titulares_limpios[:12]

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
    titulares_rss = obtener_novedades_limpias(noticias)
    bloque_rss = "\n".join([f"- {t}" for t in titulares_rss]) or "- Nuevos lanzamientos y mejoras de rendimiento en PlayStation"

    historial = cargar_historial()
    temas_usados = "\n".join([f"- {t}" for t in historial["temas"][-20:]]) or "Ninguno aún"
    ganchos_usados = "\n".join([f"- {g}" for g in historial["ganchos"][-15:]]) or "Ninguno aún"
    juegos_usados = ", ".join(historial["juegos"][-12:]) or "Ninguno aún"

    peru_tz = timezone(timedelta(hours=-5))
    fecha_hoy = datetime.now(peru_tz).strftime("%d/%m/%Y")

    prompt = f"""
    Hoy es {fecha_hoy}. Eres el guionista en ESPAÑOL LATINO de TikTok para WALFEDW SERVICES (@walfedw23).
    Hablas en primera persona: "Yo me encargo de flashear tu consola e instalarte los juegos que tú elijas".

    NOTICIAS EN ESPAÑOL DE REFERENCIA:
    {bloque_rss}

    TEMAS YA USADOS (PROHIBIDO REPETIR):
    {temas_usados}

    GANCHOS YA USADOS (PROHIBIDO REPETIR):
    {ganchos_usados}

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS DISTINTOS):
    {juegos_usados}

    REGLAS OBLIGATORIAS:
    1. TODO EL GUION DEBE ESTAR EN ESPAÑOL NATURAL (prohibido pegar frases en inglés).
    2. EXTENSIÓN: Entre 75 y 90 palabras (para que el video dure de 30 a 35 segundos).
    3. Abre con un gancho atractivo sobre novedades, lanzamientos o ahorro en PlayStation (nunca empieces con el nombre de la marca).
    4. Explica que en Walfedw Services tú flasheas la consola por software de manera cien por ciento segura (escribe "cien por ciento" en palabras, nunca uses el símbolo %) e instalas el catálogo que el cliente pida.
    5. Menciona 4 juegazos reales de PlayStation (nunca digas que PS3 corre juegos de PS4/PS5).
    6. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw, consultar la versión de su consola y decir qué juegos le gustan.
    7. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de versión/firmware.

    DEVUELVE SOLO ESTE JSON PURO:
    {{
        "tema_novedad": "Resumen corto de la novedad de hoy",
        "titulo_general": "Título del video",
        "gancho": "Primera frase del guion",
        "locucion_completa": "Texto completo en español fluido de 75 a 90 palabras.",
        "juegos_visuales": ["Juego 1", "Juego 2", "Juego 3", "Juego 4"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #PlayStation #JuegosPS4 #Walfedw"
    }}
    """

    for intento in range(1, 4):
        try:
            print(f"Intento {intento}: generando guion en español basado en novedades...")
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
                loc = datos.get("locucion_completa", "").replace("%", " por ciento").strip()
                gancho = datos.get("gancho", loc.split(".")[0]).strip()
                tema = datos.get("tema_novedad", gancho[:40]).strip()
                juegos = datos.get("juegos_visuales", [])

                es_repetido = any(gancho.lower()[:25] in prev.lower() for prev in historial["ganchos"])
                tiene_bloqueadas = any(b in loc.lower() for b in ("do not", "fpkgs", "switch", "nintendo"))

                if len(loc.split()) >= 65 and not es_repetido and not tiene_bloqueadas and len(juegos) >= 3:
                    datos["locucion_completa"] = loc
                    guardar_historial(tema, gancho, juegos)
                    print(f"Guion IA aprobado: {tema} | Juegos: {juegos}")
                    return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(2)

    # Respaldo rotativo 100% en español natural si la API externa tarda
    disponibles = [c for c in NOVEDADES_CURADAS_SPANISH if c["tema"] not in historial["temas"]]
    if not disponibles:
        disponibles = NOVEDADES_CURADAS_SPANISH
    elegido = random.choice(disponibles)

    j_lista = ", ".join(elegido["juegos"][:3]) + " y " + elegido["juegos"][3]
    loc_final = (
        f"{elegido['gancho']} "
        f"Con las últimas novedades en {elegido['detalle']}, en Walfedw Services yo me encargo de flashear tu consola por software de manera cien por ciento segura e instalarte el catálogo que tú elijas. "
        f"Desde clásicos en PS3 hasta los estrenos más pesados en PS4 y PS5 como {j_lista}, dime qué juegos te gustan y te los dejo listos. "
        f"Escríbeme hoy mismo al WhatsApp o Instagram de Walfedw y consulta la versión de tu consola."
    )

    guardar_historial(elegido["tema"], elegido["gancho"], elegido["juegos"])
    return {
        "tema_novedad": elegido["tema"],
        "titulo_general": elegido["tema"],
        "gancho": elegido["gancho"],
        "locucion_completa": loc_final,
        "juegos_visuales": elegido["juegos"],
        "hashtags": "#FlasheoPS4 #FlasheoPS5 #NovedadesPlayStation #JuegosPS4 #Walfedw"
    }
