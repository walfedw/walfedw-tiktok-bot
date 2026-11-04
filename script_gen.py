import json
import time
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico del canal @walfedw especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Novedades recopiladas:
    {texto_noticias}

    INSTRUCCIONES CLAVE DE RETENCIÓN TIKTOK:
    1. PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE (NUNCA digas "11.00", "9.00", etc.). Usa siempre "consola flasheada" o "sistema liberado".
    2. Genera una estructura completa con:
       - GANCHO INICIAL (0-3s): Pregunta/frase directa que detenga el scroll.
       - 4 ESCENAS DE CONTENIDO: Juegos indispensables o ventajas con su locución individual.
       - CIERRE CTA (3s): Pregunta final motivando a comentar o pedir catálogo por privado.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "TOP JUEGOS PS4 FLASHEADA",
        "gancho_titulo": "¿TIENES PS4 FLASHEADA?",
        "gancho_locucion": "¿Tienes tu PS4 flasheada? Guarda estos 4 juegos indispensables que debes probar ya.",
        "escenas": [
            {{
                "item": "The Last of Us Part II",
                "detalle": "Gráficos fotorrealistas y combate intenso",
                "locucion": "En el número uno, The Last of Us Part II. Una historia épica aprovechando al máximo tu consola.",
                "busqueda_imagen": "The Last of Us Part II"
            }},
            {{
                "item": "God of War Ragnarök",
                "detalle": "Batallas mitológicas y fluidez total",
                "locucion": "Número dos, God of War Ragnarök. Explora los nueve reinos con combate rápido y brutal.",
                "busqueda_imagen": "God of War Ragnarok"
            }},
            {{
                "item": "Elden Ring",
                "detalle": "Mundo abierto gigantesco y desafíos sin fin",
                "locucion": "Número tres, Elden Ring. Conquista un mundo abierto colosal en tu sistema liberado.",
                "busqueda_imagen": "Elden Ring"
            }},
            {{
                "item": "Mods y Trucos Exclusivos",
                "detalle": "Desbloquea 60 FPS, parches y cheats",
                "locucion": "Y número cuatro, Mods exclusivos. Activa 60 FPS y trucos ilimitados.",
                "busqueda_imagen": "PlayStation 4 Console"
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
                    texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()

                return json.loads(texto_respuesta)
        except Exception as e:
            print(f"Advertencia intento {intento}: {e}")
            time.sleep(3)

    raise RuntimeError("Error al conectar con la IA tras 3 intentos.")

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
