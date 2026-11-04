import os
import json
import time
import requests

HISTORIAL_FILE = "historial.json"

CATALOGO_JUEGOS_REALES = [
    {"item": "Red Dead Redemption 2", "detalle": "Mundo abierto con detalles hiperrealistas", "locucion": "En el número uno, Red Dead Redemption 2. Te flasheamos la consola y te instalamos este juegazo completo.", "busqueda_imagen": "Red Dead Redemption 2"},
    {"item": "Grand Theft Auto V", "detalle": "Acción sin límites con parches y mods", "locucion": "Número dos, Grand Theft Auto V. Liberamos tu sistema para que juegues Los Santos con catálogo lleno.", "busqueda_imagen": "Grand Theft Auto V"},
    {"item": "Bloodborne", "detalle": "Exclusivo gótico a 60 FPS", "locucion": "Número tres, Bloodborne. Flashea tu consola con nosotros y activa el parche de 60 cuadros por segundo.", "busqueda_imagen": "Bloodborne"},
    {"item": "God of War Ragnarök", "detalle": "Combate brutal y animación fluida", "locucion": "En el número uno, God of War Ragnarök. Trae tu consola a Walfedw, la liberamos e instalamos esta joya.", "busqueda_imagen": "God of War Ragnarok"},
    {"item": "The Last of Us Part II", "detalle": "Narrativa cinematográfica de alto nivel", "locucion": "Número dos, The Last of Us Part II. Disfrútalo al 100% liberando tu consola con nuestro servicio de software.", "busqueda_imagen": "The Last of Us Part II"},
    {"item": "Ghost of Tsushima", "detalle": "Japón feudal a máxima velocidad", "locucion": "Número tres, Ghost of Tsushima. Te asesoramos paso a paso para flashear tu consola y cargarte este título.", "busqueda_imagen": "Ghost of Tsushima"},
    {"item": "Elden Ring", "detalle": "Desafío de mundo abierto legendario", "locucion": "En el número uno, Elden Ring. Libera tu consola en Walfedw y juega sin límites de cuenta ni compras.", "busqueda_imagen": "Elden Ring"},
    {"item": "Spider-Man: Miles Morales", "detalle": "Acción frenética por Nueva York", "locucion": "Número dos, Spider-Man Miles Morales. Te instalamos el paquete completo de juegos en tu consola flasheada.", "busqueda_imagen": "Marvels Spider Man Miles Morales"},
    {"item": "Resident Evil 4 Remake", "detalle": "Terror y acción redefinidos", "locucion": "Número tres, Resident Evil 4 Remake. Escríbenos para liberar tu consola e instalarle los últimos estrenos.", "busqueda_imagen": "Resident Evil 4 Remake"}
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
    Eres el experto comercial del canal @walfedw especializado en servicios de FLASHEO, LIBERACIÓN Y CARGA DE JUEGOS para PS3, PS4, PS5 y Nintendo Switch.

    Novedades de la Scene:
    {texto_noticias}

    HISTORIAL DE JUEGOS USADOS (NO REPETIR):
    {string_historial}

    OBJETIVO PRINCIPAL: VENDER EL SERVICIO DE FLASHEO Y CAPTAR CLIENTES NUEVOS.
    
    REGLAS DE GUION:
    1. EL GANCHO INICIAL DEBE CAPTAR CLIENTES QUE QUIERAN FLASHEAR SU CONSOLA O CARGAR JUEGOS (Ej: "¿Quieres flashear tu PS4 o Switch?", "¿Tienes tu consola guardada sin usar? ¡Liberala en Walfedw!").
    2. En el contenido, resalta que en Walfedw realizas el flasheo profesional y la instalación del catálogo completo.
    3. PROHIBIDO MENCIONAR "MANTENIMIENTO" Y PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE.
    4. Usa nombres de juegos 100% reales.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "FLASHEO Y JUEGOS PS4 / SWITCH",
        "gancho_titulo": "¿QUIERES FLASHEAR TU CONSOLA?",
        "gancho_locucion": "¿Tienes tu PS4 o Switch guardada sin usar? En Walfedw la liberamos y te la llenamos con los mejores juegos.",
        "escenas": [
            {{
                "item": "Juego Real 1",
                "detalle": "Flasheo + Instalación de catálogo",
                "locucion": "En el número uno, [Juego 1]. Libera tu consola con nosotros e instálalo hoy mismo.",
                "busqueda_imagen": "Nombre juego en ingles"
            }},
            {{
                "item": "Juego Real 2",
                "detalle": "Juega sin pagar de más",
                "locucion": "Número dos, [Juego 2]. Disfrútalo con nuestro servicio de flasheo y carga de software.",
                "busqueda_imagen": "Nombre juego en ingles"
            }},
            {{
                "item": "Juego Real 3",
                "detalle": "Catálogo completo disponible",
                "locucion": "Número tres, [Juego 3]. Escríbenos al interno para asesorarte y liberar tu sistema.",
                "busqueda_imagen": "Nombre juego en ingles"
            }},
            {{
                "item": "Servicio de Flasheo Walfedw",
                "detalle": "Juegos, parches y mods 60 FPS",
                "locucion": "Y número cuatro, Servicio técnico de flasheo. Activa parches de 60 FPS y trucos en Walfedw.",
                "busqueda_imagen": "playstation 4 console"
            }}
        ],
        "cierre_titulo": "¡FLASHEA TU CONSOLA HOY!",
        "cierre_locucion": "¿Qué esperas para liberar tu consola? Escríbenos al privado para cotizar el flasheo y enviarte el catálogo.",
        "hashtags": "#PS4Flasheada #FlasheoPS4 #NintendoSwitch #ConsolaLiberada #walfedw"
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
                    print("Filtrando con catálogo comercial...")
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

    print("Usando catálogo comercial de respaldo...")
    no_usados = [j for j in CATALOGO_JUEGOS_REALES if j["item"] not in historial_usados]
    if len(no_usados) < 4:
        no_usados = CATALOGO_JUEGOS_REALES
    
    escenas_seleccionadas = no_usados[:4]
    guardar_historial([e["item"] for e in escenas_seleccionadas])

    return {
        "titulo_general": "FLASHEO Y JUEGOS PS4 / SWITCH",
        "gancho_titulo": "¿QUIERES FLASHEAR TU CONSOLA?",
        "gancho_locucion": "¿Tienes tu PS4 o Switch guardada sin usar? En Walfedw la liberamos y te la llenamos con los mejores juegos.",
        "escenas": escenas_seleccionadas,
        "cierre_titulo": "¡FLASHEA TU CONSOLA HOY!",
        "cierre_locucion": "¿Qué esperas para liberar tu consola? Escríbenos al privado para cotizar el flasheo y enviarte el catálogo.",
        "hashtags": "#PS4Flasheada #FlasheoPS4 #NintendoSwitch #ConsolaLiberada #walfedw"
    }

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
