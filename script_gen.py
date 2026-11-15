import os
import json
import time
import random
import requests

HISTORIAL_FILE = "historial.json"

GUIONES_VIRALES_BASE = [
    {
        "tema": "Consola guardada sin usar",
        "locucion": "Esa PS4 ahí sentada puede hacer mucho más de lo que crees. Flashéala en Walfedw para obtener miles de juegos sin costos elevados. Contáctanos hoy mismo para liberar tu consola.",
        "hashtags": "#PS4Flasheada #FlasheoPS4 #JuegosPS4 #PlayStation #Walfedw"
    },
    {
        "tema": "Dejar de gastar en discos caros",
        "locucion": "¿Sigues gastando un dineral por cada juego físico? Trae tu PS3, PS4 o PS5 a Walfedw. La liberamos por software y te la entregamos repleta con los mejores títulos listos para jugar.",
        "hashtags": "#FlasheoPS4 #PS4Liberada #JuegosGratisPS4 #PlayStationPeru #Walfedw"
    },
    {
        "tema": "Parches 60 FPS y Mods exclusivos",
        "locucion": "Tu PS4 tiene potencia oculta que no estás aprovechando. En Walfedw liberamos tu sistema, activamos parches a 60 FPS y te instalamos el catálogo completo con garantía total.",
        "hashtags": "#PS460FPS #FlasheoConsolas #PS4Flasheada #GamerPeru #Walfedw"
    },
    {
        "tema": "Sagas completas listas para jugar",
        "locucion": "God of War, Red Dead Redemption 2, Spider-Man y FC listos en tu consola sin restricciones. Escríbenos al WhatsApp de Walfedw y cotiza el flasheo de tu PS3, PS4 o PS5.",
        "hashtags": "#GodOfWar #PS4Flasheada #FlasheoPS4 #JuegosPS4 #Walfedw"
    },
    {
        "tema": "Servicio rápido y 100% seguro",
        "locucion": "No dejes tu consola juntando polvo en el cuarto. En Walfedw realizamos flasheo 100% seguro, instalación rápida de juegos y actualizaciones incluidas. Mándanos mensaje ahora.",
        "hashtags": "#ConsolaLiberada #FlasheoPS3 #FlasheoPS4 #FlasheoPS5 #Walfedw"
    }
]

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error leyendo historial: {e}")
    return []

def guardar_historial(nuevos_items):
    historial = cargar_historial()
    for item in nuevos_items:
        if item and item not in historial:
            historial.append(item)
    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
        print(f"Historial actualizado. Total acumulado: {len(historial)} elementos.")
    except Exception as e:
        print(f"Error guardando historial: {e}")

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}" for n in noticias[:6]])
    historial_usados = cargar_historial()
    string_historial = ", ".join(historial_usados[-15:]) if historial_usados else "Ninguno aún"

    prompt = f"""
    Eres el guionista viral de TikTok para @walfedw (Walfedw Services), especialista en flasheo y liberación de PS3, PS4 y PS5, carga de juegos y parches 60 FPS.

    Tendencias recientes:
    {texto_noticias}

    Temas ya usados anteriormente (NO REPETIR):
    {string_historial}

    TAREA: Escribe UN SOLO guion corto, directo y magnético de 35 a 45 palabras (13 a 16 segundos hablado) para vender el servicio de flasheo.

    REGLAS ESTRICTAS:
    1. Empieza con un gancho potente en los primeros 3 segundos (Ej: "Esa PS4 ahí sentada puede hacer mucho más de lo que crees...", "¿Sigues pagando precios absurdos por cada juego?...").
    2. Usa lenguaje natural, directo y persuasivo en español latino.
    3. PROHIBIDO mencionar números de firmware (nada de 11.00, 9.00, 12.52) y PROHIBIDO mencionar Nintendo Switch o mantenimiento.
    4. Cierra invitando a escribir al WhatsApp o Instagram de Walfedw para liberar su consola.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "Título corto del gancho",
        "locucion_completa": "El texto corrido de 35 a 45 palabras que leerá el locutor con energía.",
        "hashtags": "#PS4Flasheada #FlasheoPS4 #JuegosPS4 #PlayStation #Walfedw"
    }}
    """

    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "jsonMode": True
    }

    for intento in range(1, 4):
        try:
            print(f"Intento {intento} generando guion viral corto...")
            response = requests.post(url, json=payload, timeout=45)
            if response.status_code == 200:
                texto = response.text.strip()
                if "```json" in texto:
                    texto = texto.split("```json")[1].split("```")[0].strip()
                elif "```" in texto:
                    texto = texto.split("```")[1].split("```")[0].strip()

                datos = json.loads(texto)
                loc = datos.get("locucion_completa", "").strip()
                if len(loc.split()) >= 20:
                    guardar_historial([datos.get("titulo_general", loc[:35])])
                    return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(2)

    # Respaldo rotativo si la API tarda
    disponibles = [g for g in GUIONES_VIRALES_BASE if g["tema"] not in historial_usados]
    if not disponibles:
        disponibles = GUIONES_VIRALES_BASE
    elegido = random.choice(disponibles)
    guardar_historial([elegido["tema"]])

    return {
        "titulo_general": elegido["tema"],
        "locucion_completa": elegido["locucion"],
        "hashtags": elegido["hashtags"]
    }
