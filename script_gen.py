import os
import json
import time
import requests

HISTORIAL_FILE = "historial.json"

# Catálogo exclusivo de juegos reales de PS4 y servicios de flasheo
CATALOGO_JUEGOS_REALES = [
    {
        "item": "God of War Ragnarök",
        "detalle": "Combate brutal a 60 FPS en tu PS4",
        "locucion": "En el número uno, God of War Ragnarök. Trae tu PS4 a Walfedw, la liberamos e instalamos este juegazo completo.",
        "busqueda_imagen": "God of War Ragnarok"
    },
    {
        "item": "Red Dead Redemption 2",
        "detalle": "El mundo abierto definitivo para PS4",
        "locucion": "Número dos, Red Dead Redemption 2. Te flasheamos la consola e instalamos el mapa más detallado de la historia.",
        "busqueda_imagen": "Red Dead Redemption 2"
    },
    {
        "item": "The Last of Us Part II",
        "detalle": "Gráficos de infarto y máxima fluidez",
        "locucion": "Número tres, The Last of Us Part II. Disfruta esta obra maestra liberando tu PS4 con nuestro servicio de software.",
        "busqueda_imagen": "The Last of Us Part II"
    },
    {
        "item": "Grand Theft Auto V",
        "detalle": "Acción en Los Santos con parches y mods",
        "locucion": "En el número uno, Grand Theft Auto V. Liberamos tu PS4 para que juegues con catálogo lleno y menús de trucos.",
        "busqueda_imagen": "Grand Theft Auto V"
    },
    {
        "item": "Ghost of Tsushima",
        "detalle": "Japón feudal a máxima velocidad",
        "locucion": "Número dos, Ghost of Tsushima. Te asesoramos paso a paso para flashear tu PS4 y cargarte este título.",
        "busqueda_imagen": "Ghost of Tsushima"
    },
    {
        "item": "Bloodborne",
        "detalle": "Exclusivo imprescindible a 60 FPS",
        "locucion": "Número tres, Bloodborne. Flashea tu PS4 en Walfedw y activa el parche exclusivo de 60 cuadros por segundo.",
        "busqueda_imagen": "Bloodborne"
    },
    {
        "item": "Elden Ring",
        "detalle": "Desafío de mundo abierto sin límites",
        "locucion": "En el número uno, Elden Ring. Libera tu PS4 en Walfedw y juega sin restricciones de cuenta ni compras.",
        "busqueda_imagen": "Elden Ring"
    },
    {
        "item": "Spider-Man: Miles Morales",
        "detalle": "Acción frenética por Nueva York",
        "locucion": "Número dos, Spider-Man Miles Morales. Te instalamos el paquete completo de juegos en tu PS4 flasheada.",
        "busqueda_imagen": "Marvels Spider Man Miles Morales"
    },
    {
        "item": "Resident Evil 4 Remake",
        "detalle": "Terror y acción redefinidos en PS4",
        "locucion": "Número tres, Resident Evil 4 Remake. Escríbenos para liberar tu PS4 e instalarle los últimos estrenos.",
        "busqueda_imagen": "Resident Evil 4 Remake"
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
    string_historial = ", ".join(historial_usados[-30:]) if historial_usados else "Ninguno aún"

    prompt = f"""
    Eres el experto comercial del canal @walfedw especializado en servicios de FLASHEO, LIBERACIÓN Y CARGA DE JUEGOS PARA CONSOLAS (PS3, PS4, PS5).

    Novedades de la Scene:
    {texto_noticias}

    HISTORIAL DE JUEGOS USADOS (PROHIBIDO REPETIR):
    {string_historial}

    OBJETIVO PRINCIPAL: VENDER EL SERVICIO DE FLASHEO DE PS4 Y CAPTAR CLIENTES NUEVOS.
    
    REGLAS ESTRICTAS:
    1. PROHIBIDO MENCIONAR NINTENDO SWITCH.
    2. EL GANCHO INICIAL DEBE CAPTAR CLIENTES QUE QUIERAN FLASHEAR SU PS4 (Ej: "¿Tienes tu PS4 guardada sin usar?", "¿Quieres flashear tu PS4 y jugarlo todo?").
    3. PROHIBIDO MENCIONAR "MANTENIMIENTO" Y PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE.
    4. Usa nombres de juegos 100% reales de PS4.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "FLASHEO Y JUEGOS PS4",
        "gancho_titulo": "¿TIENES TU PS4 SIN FLASHEAR?",
        "gancho_locucion": "¿Tienes tu PS4 guardada sin usar? En Walfedw la liberamos hoy mismo y te la entregamos con los mejores juegos.",
        "escenas": [
            {{
                "item": "Nombre Juego Real 1",
                "detalle": "Flasheo + Instalación de catálogo",
                "locucion": "En el número uno, [Juego 1]. Libera tu PS4 con nosotros e instálalo hoy mismo.",
                "busqueda_imagen": "Nombre juego en ingles"
            }},
            {{
                "item": "Nombre Juego Real 2",
                "detalle": "Juega sin pagar de más",
                "locucion": "Número dos, [Juego 2]. Disfrútalo en tu PS4 con nuestro servicio de flasheo y software.",
                "busqueda_imagen": "Nombre juego en ingles"
            }},
            {{
                "item": "Nombre Juego Real 3",
                "detalle": "Catálogo completo disponible",
                "locucion": "Número tres, [Juego 3]. Escríbenos al privado para asesorarte y liberar tu sistema PS4.",
                "busqueda_imagen": "Nombre juego en ingles"
            }},
            {{
                "item": "Servicio de Flasheo PS4",
                "detalle": "Juegos, parches y mods 60 FPS",
                "locucion": "Y número cuatro, Servicio técnico de flasheo. Activa parches de 60 FPS y trucos en Walfedw.",
                "busqueda_imagen": "playstation 4 controller neon"
            }}
        ],
        "cierre_titulo": "¡FLASHEA TU PS4 HOY!",
        "cierre_locucion": "¿Qué esperas para liberar tu PS4? Escríbenos al privado para cotizar el flasheo y enviarte el catálogo.",
        "hashtags": "#PS4Flasheada #FlasheoPS4 #JuegosPS4 #ConsolaLiberada #walfedw"
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
                    if "underworld" in nombre or "phantom" in nombre or "simucraft" in nombre or "nombre juego" in nombre:
                        juegos_validos = False
                        break
                
                if not juegos_validos or len(escenas_recibidas) < 3:
                    print("Aplicando catálogo filtrado de PS4...")
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

    print("Usando catálogo PS4 de respaldo...")
    no_usados = [j for j in CATALOGO_JUEGOS_REALES if j["item"] not in historial_usados]
    if len(no_usados) < 4:
        no_usados = CATALOGO_JUEGOS_REALES
    
    escenas_seleccionadas = no_usados[:4]
    guardar_historial([e["item"] for e in escenas_seleccionadas])

    return {
        "titulo_general": "FLASHEO Y JUEGOS PS4",
        "gancho_titulo": "¿TIENES TU PS4 SIN FLASHEAR?",
        "gancho_locucion": "¿Tienes tu PS4 guardada sin usar? En Walfedw la liberamos hoy mismo y te la entregamos con los mejores juegos.",
        "escenas": escenas_seleccionadas,
        "cierre_titulo": "¡FLASHEA TU PS4 HOY!",
        "cierre_locucion": "¿Qué esperas para liberar tu PS4? Escríbenos al privado para cotizar el flasheo y enviarte el catálogo.",
        "hashtags": "#PS4Flasheada #FlasheoPS4 #JuegosPS4 #ConsolaLiberada #walfedw"
    }

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
