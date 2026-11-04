import os
import json
import time
import requests

HISTORIAL_FILE = "historial.json"

ESCENAS_RESPALDO = [
    {
        "item": "Red Dead Redemption 2",
        "detalle": "Mundo abierto colosal y detalles realistas",
        "locucion": "En el número uno, Red Dead Redemption 2. Una obra maestra del mundo abierto en tu consola liberada.",
        "busqueda_imagen": "Red Dead Redemption 2"
    },
    {
        "item": "Spider-Man: Miles Morales",
        "detalle": "Acción frenética a máxima velocidad",
        "locucion": "Número dos, Spider-Man Miles Morales. Gráficos espectaculares y balanceo fluido.",
        "busqueda_imagen": "Marvels Spider Man Miles Morales"
    },
    {
        "item": "Cyberpunk 2077",
        "detalle": "Night City con rendimiento optimizado",
        "locucion": "Número tres, Cyberpunk 2077. Disfruta Night City con todos sus parches en tu sistema liberado.",
        "busqueda_imagen": "Cyberpunk 2077"
    },
    {
        "item": "Mods y Trucos Exclusivos",
        "detalle": "Desbloquea 60 FPS, parches y cheats",
        "locucion": "Y número cuatro, Mods exclusivos. Activa 60 FPS y trucos ilimitados en Walfedw.",
        "busqueda_imagen": "PlayStation 4 Setup"
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
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])
    historial_usados = cargar_historial()
    string_historial = ", ".join(historial_usados[-20:]) if historial_usados else "Ninguno aún"

    prompt = f"""
    Eres el experto técnico del canal @walfedw especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Novedades recopiladas:
    {texto_noticias}

    ELEMENTOS YA UTILIZADOS ANTERIORMENTE (PROHIBIDO REPETIR ESTOS NOMBRES):
    {string_historial}

    INSTRUCCIONES CLAVE DE RETENCIÓN TIKTOK:
    1. PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE (NUNCA digas "11.00", "9.00", etc.). Usa "consola flasheada" o "sistema liberado".
    2. NUNCA elijas un juego o tema presente en la lista de elementos ya utilizados.
    3. CADA ESCENA DEBE SER UN JUEGO DISTINTO O UTILIDAD CON SU PROPIA LOCUCIÓN.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "TOP JUEGOS PS4 FLASHEADA",
        "gancho_titulo": "¿TIENES PS4 FLASHEADA?",
        "gancho_locucion": "¿Tienes tu PS4 flasheada? Guarda estos 4 juegos indispensables que debes probar ya.",
        "escenas": [
            {{
                "item": "Nombre del Juego 1",
                "detalle": "Detalle llamativo corto",
                "locucion": "En el número uno, Nombre del Juego 1 y sus características.",
                "busqueda_imagen": "Nombre del Juego 1"
            }},
            {{
                "item": "Nombre del Juego 2",
                "detalle": "Detalle llamativo corto",
                "locucion": "Número dos, Nombre del Juego 2 y su rendimiento.",
                "busqueda_imagen": "Nombre del Juego 2"
            }},
            {{
                "item": "Nombre del Juego 3",
                "detalle": "Detalle llamativo corto",
                "locucion": "Número tres, Nombre del Juego 3 en tu sistema liberado.",
                "busqueda_imagen": "Nombre del Juego 3"
            }},
            {{
                "item": "Mods y Trucos Exclusivos",
                "detalle": "Desbloquea 60 FPS y cheats",
                "locucion": "Y número cuatro, Mods exclusivos. Activa 60 FPS y trucos ilimitados en Walfedw.",
                "busqueda_imagen": "PlayStation 4 Setup"
            }}
        ],
        "cierre_titulo": "¿CUÁL ES TU FAVORITO?",
        "cierre_locucion": "¿Cuál es tu favorito? Comenta aquí abajo o escríbenos al privado para el catálogo completo.",
        "hashtags": "#PS4Flasheada #JuegosPS4 #NintendoSwitch #ConsolaLiberada #walfedw"
    }}
    """

    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "jsonMode": True
    }

    for intento in range(1, 4):
        try:
            print(f"Intento {intento} solicitando guion a la IA...")
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                texto_respuesta = response.text.strip()
                if "```json" in texto_respuesta:
                    texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
                elif "```" in texto_respuesta:
                    texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()

                datos = json.loads(texto_respuesta)
                
                # Validar que contenga al menos 3 escenas válidas
                escenas_recibidas = datos.get("escenas", [])
                if not escenas_recibidas or len(escenas_recibidas) < 3:
                    print("Advertencia: IA devolvió escenas insuficientes. Aplicando escenas de respaldo...")
                    datos["escenas"] = ESCENAS_RESPALDO
                
                nuevos = [e.get("item") for e in datos.get("escenas", []) if e.get("item")]
                guardar_historial(nuevos)
                
                return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(3)

    print("Error conectando con la IA. Generando video con datos de respaldo de alta calidad...")
    return {
        "titulo_general": "TOP JUEGOS PS4 FLASHEADA",
        "gancho_titulo": "¿TIENES PS4 FLASHEADA?",
        "gancho_locucion": "¿Tienes tu PS4 flasheada? Guarda estos 4 juegos indispensables que debes probar ya.",
        "escenas": ESCENAS_RESPALDO,
        "cierre_titulo": "¿CUÁL ES TU FAVORITO?",
        "cierre_locucion": "¿Cuál es tu favorito? Comenta aquí abajo o escríbenos al privado para el catálogo completo.",
        "hashtags": "#PS4Flasheada #JuegosPS4 #NintendoSwitch #ConsolaLiberada #walfedw"
    }

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
