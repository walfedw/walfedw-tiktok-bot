import os
import json
import time
import random
from datetime import datetime, timezone, timedelta
import requests

HISTORIAL_FILE = "historial.json"

def obtener_novedades_en_vivo(noticias_rss):
    """Combina las noticias del RSS con tendencias reales de PlayStation y Scene."""
    titulares = [n["titulo"] for n in (noticias_rss or []) if n.get("titulo")]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WalfedwNewsBot/1.0"}

    fuentes_live = [
        "https://www.reddit.com/r/ps4homebrew/hot.json?limit=12",
        "https://www.reddit.com/r/PS5/hot.json?limit=12",
        "https://www.reddit.com/r/PS4/hot.json?limit=10"
    ]
    for url in fuentes_live:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                posts = r.json().get("data", {}).get("children", [])
                for p in posts:
                    data = p.get("data", {})
                    if not data.get("stickied") and not data.get("over_18"):
                        t = data.get("title", "").strip()
                        if t and t not in titulares:
                            titulares.append(t)
        except Exception:
            continue

    return titulares[:25]

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

    # Memoria amplia: no repite temas ni juegos usados en los últimos videos
    historial["temas"] = historial["temas"][-50:]
    historial["ganchos"] = historial["ganchos"][-50:]
    historial["juegos"] = historial["juegos"][-24:]

    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando historial: {e}")

def generar_guion(noticias):
    novedades = obtener_novedades_en_vivo(noticias)
    bloque_novedades = "\n".join([f"- {t}" for t in novedades]) or "- Nuevos lanzamientos y parches de rendimiento en PlayStation"

    historial = cargar_historial()
    temas_usados = "\n".join([f"- {t}" for t in historial["temas"][-20:]]) or "Ninguno aún"
    ganchos_usados = "\n".join([f"- {g}" for g in historial["ganchos"][-15:]]) or "Ninguno aún"
    juegos_usados = ", ".join(historial["juegos"][-16:]) or "Ninguno aún"

    peru_tz = timezone(timedelta(hours=-5))
    fecha_hoy = datetime.now(peru_tz).strftime("%d/%m/%Y")

    prompt = f"""
    Hoy es {fecha_hoy}. Eres el estratega y guionista principal de TikTok para WALFEDW SERVICES (@walfedw23).
    Tu trabajo es analizar las NOVEDADES REALES DEL DÍA en el mundo PlayStation y crear un guion único, fresco y vendedor.

    NOVEDADES Y TENDENCIAS REALES RECIENTES:
    {bloque_novedades}

    TEMAS YA USADOS EN VIDEOS ANTERIORES (PROHIBIDO REPETIR):
    {temas_usados}

    GANCHOS YA USADOS (PROHIBIDO REPETIR):
    {ganchos_usados}

    JUEGOS YA MOSTRADOS RECIENTEMENTE (ELIGE OTROS JUEGOS DISTINTOS DE PLAYSTATION):
    {juegos_usados}

    TU MISIÓN CREATIVA:
    1. Elige UNA novedad, lanzamiento, tendencia o avance real de la lista de arriba que NO esté en los temas ya usados.
    2. Escribe un guion natural, atractivo y directo de 75 a 90 palabras (para que el video dure entre 30 y 35 segundos).
    3. Estructura del guion:
       - Abre con un gancho sobre la novedad del día o una pregunta directa que detenga el scroll (NUNCA empieces con el nombre de la marca).
       - Conecta esa novedad con tu servicio: explica en primera persona que en Walfedw Services tú te encargas de flashear la consola por software de forma 100% segura e instalar los juegos que el cliente pida.
       - Menciona 3 o 4 juegazos reales de PlayStation (distintos a los ya usados) que encajen con el tema.
       - Cierra invitando al espectador a escribirte al WhatsApp o Instagram de Walfedw, consultar la versión de su consola y decirte qué juegos le gustan.

    REGLAS ESTRICTAS:
    - COHERENCIA TÉCNICA: Nunca digas que una PS3 corre juegos modernos de PS4/PS5. Escribe "PS3, PS4 y PS5" separado por comas.
    - PROHIBIDO mencionar Nintendo Switch y PROHIBIDO mencionar números de versión/firmware (nada de 9.00, 11.00, 12.52).
    - En "juegos_visuales" pon los nombres oficiales en inglés de 4 juegos reales de PlayStation mencionados o relacionados con el guion para buscar sus gameplays automáticamente.

    DEVUELVE ÚNICAMENTE ESTE JSON PURO:
    {{
        "tema_novedad": "Resumen de 5 palabras de la novedad elegida hoy",
        "titulo_general": "Título atractivo del video",
        "gancho": "La primera frase exacta del guion",
        "locucion_completa": "Texto completo y fluido de 75 a 90 palabras.",
        "juegos_visuales": ["Juego Real 1", "Juego Real 2", "Juego Real 3", "Juego Real 4"],
        "hashtags": "#FlasheoPS4 #PS4Flasheada #PlayStation #JuegosPS4 #Walfedw"
    }}
    """

    for intento in range(1, 4):
        try:
            print(f"Intento {intento}: IA analizando novedades reales del día...")
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
                tema = datos.get("tema_novedad", gancho[:40]).strip()
                juegos = datos.get("juegos_visuales", [])

                es_repetido = any(gancho.lower()[:25] in prev.lower() for prev in historial["ganchos"])
                tiene_switch = "switch" in loc.lower() or "nintendo" in loc.lower()

                if len(loc.split()) >= 65 and not es_repetido and not tiene_switch and len(juegos) >= 3:
                    guardar_historial(tema, gancho, juegos)
                    print(f"Novedad elegida por la IA: {tema} | Juegos: {juegos}")
                    return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(2)

    # Respaldo dinámico usando el titular real más reciente del feed
    titular_hoy = novedades[0][:70] if novedades else "los últimos estrenos y parches a 60 FPS en PlayStation"
    juegos_backup = ["Black Myth Wukong", "Tekken 8", "Gran Turismo 7", "Bloodborne"]
    loc_backup = (
        f"¿Ya viste lo último que está pasando con {titular_hoy}? "
        f"Si quieres disfrutar los mejores títulos sin gastar una fortuna por cada disco, en Walfedw Services yo me encargo de flashear tu consola por software de manera 100% segura e instalarte el catálogo que tú elijas. "
        f"Desde clásicos en PS3 hasta los estrenos más pesados en PS4 y PS5, dime qué juegos te gustan y te los dejo listos. "
        f"Escríbeme hoy mismo al WhatsApp o Instagram de Walfedw y consulta la versión de tu consola."
    )
    guardar_historial(titular_hoy[:35], loc_backup[:40], juegos_backup)
    return {
        "tema_novedad": titular_hoy[:35],
        "titulo_general": "Novedades PlayStation y Flasheo",
        "gancho": loc_backup.split("?")[0] + "?",
        "locucion_completa": loc_backup,
        "juegos_visuales": juegos_backup,
        "hashtags": "#FlasheoPS4 #FlasheoPS5 #NovedadesPlayStation #JuegosPS4 #Walfedw"
    }
