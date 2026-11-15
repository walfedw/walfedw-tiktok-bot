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
        "tema": "Juegazos de acción y mundo abierto para PS4 y PS3",
        "gancho": "¿Tienes una PS4 o PS3 en casa y sigues pagando carísimo por cada juego?",
        "detalle": "aventuras gigantescas y catálogos completos listos para jugar sin discos",
        "juegos": ["God of War Ragnarok", "Ghost of Tsushima", "Red Dead Redemption 2", "Days Gone"]
    },
    {
        "tema": "Parches a 60 FPS y mejoras en PS4 liberada",
        "gancho": "¿Sabías que en tu PS4 puedes activar parches a 60 FPS y menús de mods exclusivos?",
        "detalle": "las mejoras de fluidez y rendimiento que desbloquean todo el poder de tu consola",
        "juegos": ["Red Dead Redemption 2", "Bloodborne", "Grand Theft Auto V", "The Last of Us Part I"]
    },
    {
        "tema": "Terror y supervivencia al máximo en PS4",
        "gancho": "Si te gustan los juegos de terror y acción intensa, mira lo que puedes instalar en tu PS4.",
        "detalle": "títulos cargados de adrenalina con todos sus DLC y expansiones incluidas",
        "juegos": ["Resident Evil 4", "Cyberpunk 2077", "Elden Ring", "Mortal Kombat 11"]
    },
    {
        "tema": "Peleas, fútbol y anime para jugar con amigos en PS4 y PS3",
        "gancho": "Convierte tu PS4 o PS3 en la consola definitiva para jugar con tus patas este fin de semana.",
        "detalle": "los mejores títulos de fútbol, peleas y anime listos en tu disco duro",
        "juegos": ["Dragon Ball Z Kakarot", "Naruto Shippuden Ultimate Ninja Storm 4", "Marvels Spider-Man Remastered", "EA SPORTS FC 24"]
    },
    {
        "tema": "Rescate total de consolas PS4 y PS3 guardadas",
        "gancho": "Si tienes tu PS4 o PS3 juntando polvo en tu cuarto, dale una segunda vida hoy mismo.",
        "detalle": "la liberación por software más limpia y segura para llenar tu consola de éxitos",
        "juegos": ["Horizon Forbidden West", "Sekiro Shadows Die Twice", "Dark Souls III", "Grand Theft Auto V"]
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
    bloque_rss = "\n".join([f"- {t}" for t in titulares_rss]) or "- Nuevos parches y catálogos disponibles para PS4 y PS3"

    historial = cargar_historial()
    temas_usados = "\n".join([f"- {t}" for t in historial["temas"][-20:]]) or "Ninguno aún"
    ganchos_usados = "\n".join([f"- {g}" for g in historial["ganchos"][-15:]]) or "Ninguno aún"
    juegos_usados = ", ".join(historial["juegos"][-12:]) or "Ninguno aún"

    peru_tz = timezone(timedelta(hours=-5))
    fecha_hoy = datetime.now(peru_tz).strftime("%d/%m/%Y")

    prompt = f"""
    Hoy es {fecha_hoy}. Eres el guionista en ESPAÑOL LATINO de TikTok para WALFEDW SERVICES (@walfedw23).
    Hablas en primera persona: "Yo me encargo de flashear tu consola e instalarte los juegos que tú elijas".

    NOTICIAS DE REFERENCIA:
    {bloque_rss}

    TEMAS YA USADOS (PROHIBIDO REPETIR):
    {temas_usados}

    GANCHOS YA USADOS (PROHIBIDO REPETIR):
    {ganchos_usados}

    JUEGOS USADOS RECIENTEMENTE (ELIGE OTROS DISTINTOS):
    {juegos_usados}

    REGLAS OBLIGATORIAS DE PRIORIDAD DE CONSOLAS:
    1. ENFOQUE PRINCIPAL: Dale 80% de protagonismo a **PS4** y 20% a **PS3** (son nuestros clientes principales). Menciona **PS5** solo de paso al final como "y también soportamos PS5", o ni siquiera le des peso.
    2. JUEGOS COMPATIBLES: Elige 4 juegazos reales que existan en **PS4** (y clásicos en **PS3**). PROHIBIDO poner exclusivos que solo existen en PS5 (nada de Spider-Man 2 ni Black Myth Wukong).
    3. TODO EN ESPAÑOL NATURAL (cero frases en inglés).
    4. EXTENSIÓN: Entre 75 y 90 palabras (para que el video dure de 30 a 35 segundos).
    5. Abre con un gancho directo dirigido a dueños de PS4 o PS3 (nunca empieces con el nombre de la marca).
    6. Explica que en Walfedw Services tú flasheas la consola por software de manera cien por ciento segura (escribe "cien por ciento" en palabras, nunca uses %) e instalas los juegos, DLC y parches a 60 FPS que pidan.
    7. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw, consultar la versión de su consola y decir qué juegos le gustan.
    8. PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de versión/firmware.

    DEVUELVE SOLO ESTE JSON PURO:
    {{
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
            print(f"Intento {intento}: generando guion enfocado en PS4 y PS3...")
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
                tiene_bloqueadas = any(b in loc.lower() for b in ("do not", "fpkgs", "switch", "nintendo", "spider-man 2", "wukong"))

                if len(loc.split()) >= 65 and not es_repetido and not tiene_bloqueadas and len(juegos) >= 3:
                    datos["locucion_completa"] = loc
                    guardar_historial(tema, gancho, juegos)
                    print(f"Guion IA aprobado (PS4/PS3): {tema} | Juegos: {juegos}")
                    return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(2)

    disponibles = [c for c in NOVEDADES_CURADAS_SPANISH if c["tema"] not in historial["temas"]]
    if not disponibles:
        disponibles = NOVEDADES_CURADAS_SPANISH
    elegido = random.choice(disponibles)

    j_lista = ", ".join(elegido["juegos"][:3]) + " y " + elegido["juegos"][3]
    loc_final = (
        f"{elegido['gancho']} "
        f"Con {elegido['detalle']}, en Walfedw Services yo me encargo de flashear tu PS4 o PS3 por software de manera cien por ciento segura e instalarte el catálogo que tú elijas, y también damos soporte para PS5. "
        f"Disfruta joyas brutales como {j_lista} listas para jugar sin restricciones. "
        f"Dime qué juegos te gustan, escríbeme hoy mismo al WhatsApp o Instagram de Walfedw y consulta la versión de tu consola."
    )

    guardar_historial(elegido["tema"], elegido["gancho"], elegido["juegos"])
    return {
        "tema_novedad": elegido["tema"],
        "titulo_general": elegido["tema"],
        "gancho": elegido["gancho"],
        "locucion_completa": loc_final,
        "juegos_visuales": elegido["juegos"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #FlasheoPS3 #JuegosPS4 #Walfedw"
    }
