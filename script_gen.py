import os
import json
import time
import requests

HISTORIAL_FILE = "historial.json"

# Catálogo con juegos 100% reales para garantizar imágenes oficiales y locución natural
CATALOGO_JUEGOS_REALES = [
    {"item": "God of War Ragnarök", "detalle": "Combate épico y gráficos brutales", "locucion": "En el número uno, God of War Ragnarök. Vive la batalla final de Kratos con fluidez total en tu consola liberada.", "busqueda_imagen": "God of War Ragnarok"},
    {"item": "The Last of Us Part II", "detalle": "Historia intensa y combate realista", "locucion": "Número dos, The Last of Us Part II. Una experiencia cinematográfica impactante que explota tu PS4 al máximo.", "busqueda_imagen": "The Last of Us Part II"},
    {"item": "Ghost of Tsushima", "detalle": "Mundo abierto samurai a 60 FPS", "locucion": "Número tres, Ghost of Tsushima. Domina la katana en el Japón feudal con rendimiento espectacular.", "busqueda_imagen": "Ghost of Tsushima"},
    {"item": "Red Dead Redemption 2", "detalle": "El salvaje oeste definitivo", "locucion": "En el número uno, Red Dead Redemption 2. Explora el mapa más detallado de la historia en tu sistema liberado.", "busqueda_imagen": "Red Dead Redemption 2"},
    {"item": "Spider-Man: Miles Morales", "detalle": "Acción frenética por Nueva York", "locucion": "Número dos, Spider-Man Miles Morales. Balancéate a máxima velocidad con efectos visuales impresionantes.", "busqueda_imagen": "Spider-Man Miles Morales"},
    {"item": "Bloodborne", "detalle": "El clásico exclusivo imprescindible", "locucion": "Número tres, Bloodborne. Enfrenta pesadillas góticas con el parche de 60 cuadros por segundo exclusivo.", "busqueda_imagen": "Bloodborne"},
    {"item": "Elden Ring", "detalle": "Desafío colosal de mundo abierto", "locucion": "En el número uno, Elden Ring. Conquista las Tierras Intermedias sin restricciones en tu consola flasheada.", "busqueda_imagen": "Elden Ring"},
    {"item": "Resident Evil 4 Remake", "detalle": "Terror y acción de última generación", "locucion": "Número dos, Resident Evil 4 Remake. Revive un clásico de leyenda con gráficos de infarto.", "busqueda_imagen": "Resident Evil 4 Remake"},
    {"item": "GTA V (Grand Theft Auto V)", "detalle": "Caos total con menú de mods", "locucion": "Número tres, GTA 5. Instala menús de trucos y mods de vehículos para divertirte sin límites.", "busqueda_imagen": "Grand Theft Auto V"}
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
    string_historial = ", ".join(historial_usados[-30:]) if historial_usados else "Ninguno aún"

    prompt = f"""
    Eres el experto técnico del canal @walfedw especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Noticias recientes de la comunidad:
    {texto_noticias}

    HISTORIAL DE JUEGOS YA USADOS (¡PROHIBIDO REPETIR ESTOS NOMBRES!):
    {string_historial}

    REGLAS ESTRICTAS E IMPRESCINDIBLES:
    1. USAR ÚNICAMENTE JUEGOS REALES Y FAMOSOS DE PLAYSTATION O SWITCH (Ejemplos: Bloodborne, Red Dead Redemption 2, GTA V, Elden Ring, God of War Ragnarok, Resident Evil 4 Remake, Spider-Man, Ghost of Tsushima, FIFA, Horizon, The Last of Us, Zelda, Mario, etc.).
    2. ¡PROHIBIDO INVENTAR JUEGOS QUE NO EXISTAN!
    3. PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE (NUNCA digas "11.00", "9.00", etc.). Usa "consola flasheada" o "sistema liberado".
    4. Redacta locuciones naturales, dinámicas y con energía comercial en ESPAÑOL LATINO. No uses frases robóticas.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "TOP JUEGOS PS4 FLASHEADA",
        "gancho_titulo": "¿TIENES PS4 FLASHEADA?",
        "gancho_locucion": "¿Tienes tu PS4 flasheada? Guarda estos 3 juegos indispensables que debes probar ya.",
        "escenas": [
            {{
                "item": "Nombre Exacto de Juego Real 1",
                "detalle": "Resumen corto de beneficio",
                "locucion": "En el número uno, [Nombre del Juego 1] y su explicación entusiasta.",
                "busqueda_imagen": "Nombre del juego en inglés para RAWG"
            }},
            {{
                "item": "Nombre Exacto de Juego Real 2",
                "detalle": "Resumen corto de beneficio",
                "locucion": "Número dos, [Nombre del Juego 2] y su explicación entusiasta.",
                "busqueda_imagen": "Nombre del juego en inglés para RAWG"
            }},
            {{
                "item": "Nombre Exacto de Juego Real 3",
                "detalle": "Resumen corto de beneficio",
                "locucion": "Número tres, [Nombre del Juego 3] y su explicación entusiasta.",
                "busqueda_imagen": "Nombre del juego en inglés para RAWG"
            }},
            {{
                "item": "Mods y Trucos Exclusivos",
                "detalle": "Desbloquea 60 FPS y cheats",
                "locucion": "Y número cuatro, Mods exclusivos. Activa parches de 60 FPS y trucos ilimitados en Walfedw.",
                "busqueda_imagen": "PlayStation 4 Console"
            }}
        ],
        "cierre_titulo": "¿CUÁL ES TU FAVORITO?",
        "cierre_locucion": "¿Cuál es tu favorito? Comenta aquí abajo o escríbenos al privado para enviarte el catálogo completo.",
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
                    texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()

                datos = json.loads(texto_respuesta)
                escenas_recibidas = datos.get("escenas", [])
                
                # Verificar si la IA devolvió juegos inventados o genéricos
                juegos_validos = True
                for esc in escenas_recibidas:
                    nombre = esc.get("item", "").lower()
                    if "underworld" in nombre or "phantom drive" in nombre or "simucraft" in nombre or "nombre del juego" in nombre:
                        juegos_validos = False
                        break
                
                if not juegos_validos or len(escenas_recibidas) < 3:
                    print("Advertencia: IA devolvió nombres genéricos/inventados. Filtrando con catálogo de juegos reales...")
                    no_usados = [j for j in CATALOGO_JUEGOS_REALES if j["item"] not in historial_usados]
                    if len(no_usados) < 4:
                        no_usados = CATALOGO_JUEGOS_REALES
                    datos["escenas"] = no_usados[:4]

                nuevos = [e.get("item") for e in datos.get("escenas", []) if e.get("item")]
                guardar_historial(nuevos)
                return datos
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(3)

    print("Usando juegos de respaldo del catálogo real...")
    no_usados = [j for j in CATALOGO_JUEGOS_REALES if j["item"] not in historial_usados]
    if len(no_usados) < 4:
        no_usados = CATALOGO_JUEGOS_REALES
    
    escenas_seleccionadas = no_usados[:4]
    guardar_historial([e["item"] for e in escenas_seleccionadas])

    return {
        "titulo_general": "TOP JUEGOS PS4 FLASHEADA",
        "gancho_titulo": "¿TIENES PS4 FLASHEADA?",
        "gancho_locucion": "¿Tienes tu PS4 flasheada? Guarda estos 3 juegos indispensables que debes probar ya.",
        "escenas": escenas_seleccionadas,
        "cierre_titulo": "¿CUÁL ES TU FAVORITO?",
        "cierre_locucion": "¿Cuál es tu favorito? Comenta aquí abajo o escríbenos al privado para enviarte el catálogo completo.",
        "hashtags": "#PS4Flasheada #JuegosPS4 #NintendoSwitch #ConsolaLiberada #walfedw"
    }

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
