import os
import json
import time
import requests

HISTORIAL_FILE = "historial.json"

# Catálogo exclusivo de juegos reales y servicios de flasheo/software
CATALOGO_JUEGOS_REALES = [
    {"item": "Red Dead Redemption 2", "detalle": "Mundo abierto con detalles hiperrealistas", "locucion": "En el número uno, Red Dead Redemption 2. Explora el mapa más detallado de la historia en tu consola liberada.", "busqueda_imagen": "Red Dead Redemption 2"},
    {"item": "Grand Theft Auto V", "detalle": "Acción sin límites con parches y mods", "locucion": "Número dos, Grand Theft Auto V. Disfruta de Los Santos con fluidez y catálogo completo en tu sistema flasheado.", "busqueda_imagen": "Grand Theft Auto V"},
    {"item": "Bloodborne", "detalle": "Exclusivo gótico a 60 FPS", "locucion": "Número tres, Bloodborne. Desbloquea la experiencia gótica definitiva con el parche de 60 cuadros por segundo.", "busqueda_imagen": "Bloodborne"},
    {"item": "God of War Ragnarök", "detalle": "Combate brutal y animación fluida", "locucion": "En el número uno, God of War Ragnarök. Vive la batalla final de Kratos aprovechando al máximo tu consola liberada.", "busqueda_imagen": "God of War Ragnarok"},
    {"item": "The Last of Us Part II", "detalle": "Narrativa cinematográfica de alto nivel", "locucion": "Número dos, The Last of Us Part II. Una historia impactante con gráficos que explotan el potencial de tu consola.", "busqueda_imagen": "The Last of Us Part II"},
    {"item": "Ghost of Tsushima", "detalle": "Japón feudal a máxima velocidad", "locucion": "Número tres, Ghost of Tsushima. Domina la katana en un mundo abierto espectacular sin restricciones de software.", "busqueda_imagen": "Ghost of Tsushima"},
    {"item": "Elden Ring", "detalle": "Desafío de mundo abierto legendario", "locucion": "En el número uno, Elden Ring. Conquista las Tierras Intermedias con total libertad en tu sistema liberado.", "busqueda_imagen": "Elden Ring"},
    {"item": "Spider-Man: Miles Morales", "detalle": "Acción frenética por Nueva York", "locucion": "Número dos, Spider-Man Miles Morales. Balancéate por la ciudad con rendimiento impecable en tu consola.", "busqueda_imagen": "Marvels Spider Man Miles Morales"},
    {"item": "Resident Evil 4 Remake", "detalle": "Terror y acción redefinidos", "locucion": "Número tres, Resident Evil 4 Remake. Revive este clásico de leyenda con gráficos fotorrealistas en Walfedw.", "busqueda_imagen": "Resident Evil 4 Remake"}
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

    REGLAS ESTRICTAS:
    1. PROHIBIDO MENCIONAR LA PALABRA MANTENIMIENTO. Enfócate SOLO en Flasheo, Liberación, Catálogo de Juegos y Software.
    2. Usa únicamente nombres de juegos 100% reales de PlayStation y Switch.
    3. PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE (Usa "consola flasheada" o "sistema liberado").
    4. Redacta locuciones comerciales dinámicas con voz en vivo estilo gamer.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "TOP JUEGOS PS4 FLASHEADA",
        "gancho_titulo": "¿TIENES PS4 FLASHEADA?",
        "gancho_locucion": "¿Tienes tu PS4 flasheada? Guarda estos 3 juegos indispensables que debes probar ya.",
        "escenas": [
            {{
                "item": "Nombre del Juego 1",
                "detalle": "Beneficio de jugarlo liberado",
                "locucion": "En el número uno, [Nombre 1] y su explicación comercial.",
                "busqueda_imagen": "Nombre del juego en inglés para RAWG"
            }},
            {{
                "item": "Nombre del Juego 2",
                "detalle": "Beneficio de jugarlo liberado",
                "locucion": "Número dos, [Nombre 2] y su explicación comercial.",
                "busqueda_imagen": "Nombre del juego en inglés para RAWG"
            }},
            {{
                "item": "Nombre del Juego 3",
                "detalle": "Beneficio de jugarlo liberado",
                "locucion": "Número tres, [Nombre 3] y su explicación comercial.",
                "busqueda_imagen": "Nombre del juego en inglés para RAWG"
            }},
            {{
                "item": "Mods y Parches de Software",
                "detalle": "Desbloquea 60 FPS y cheats",
                "locucion": "Y número cuatro, Parches de software exclusivos. Activa 60 FPS y trucos en Walfedw.",
                "busqueda_imagen": "PlayStation 4 Console"
            }}
        ],
        "cierre_titulo": "¿CUÁL ES TU FAVORITO?",
        "cierre_locucion": "¿Cuál es tu favorito? Comenta aquí abajo o escríbenos al privado para la instalación de juegos y flasheo.",
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
                
                juegos_validos = True
                for esc in escenas_recibidas:
                    nombre = esc.get("item", "").lower()
                    if "underworld" in nombre or "phantom" in nombre or "simucraft" in nombre or "nombre del juego" in nombre:
                        juegos_validos = False
                        break
                
                if not juegos_validos or len(escenas_recibidas) < 3:
                    print("Filtrando con catálogo oficial de juegos reales...")
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

    print("Usando juegos del catálogo real...")
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
