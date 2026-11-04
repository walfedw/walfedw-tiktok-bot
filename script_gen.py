import json
import time
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico del canal @walfedw especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Tendencias de la comunidad:
    {texto_noticias}

    INSTRUCCIONES CLAVE:
    1. PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE (NUNCA digas "11.00", "9.00", etc.). Usa siempre "consola flasheada" o "sistema liberado".
    2. Crea un video en 4 ESCENAS INDIVIDUALES.
    3. CADA ESCENA DEBE TENER SU PROPIO TEXTO DE LOCUCIÓN ("texto_locucion") para que la voz coincida EXACTAMENTE con el juego o tema que está en pantalla.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "titulo_general": "TOP JUEGOS INDISPENSABLES PS4 FLASHEADA",
        "escenas": [
            {{
                "item": "Resident Evil 4 Remake",
                "detalle": "Gráficos de última generación y terror absoluto",
                "texto_locucion": "En el número uno, Resident Evil 4 Remake. Gráficos brutales y terror en tu consola flasheada.",
                "busqueda_imagen": "Resident Evil 4 Remake"
            }},
            {{
                "item": "Ghost of Tsushima",
                "detalle": "Mundo abierto samurai en fluidez total",
                "texto_locucion": "Número dos, Ghost of Tsushima. Explora el Japón feudal con combate rápido y cinemáticas espectaculares.",
                "busqueda_imagen": "Ghost of Tsushima"
            }},
            {{
                "item": "Uncharted 4: A Thief's End",
                "detalle": "Aventura de acción cinematográfica imperdible",
                "texto_locucion": "Número tres, Uncharted 4. Una historia cinematográfica que explota al máximo la potencia de tu consola.",
                "busqueda_imagen": "Uncharted 4 A Thiefs End"
            }},
            {{
                "item": "Mods y Trucos Exclusivos",
                "detalle": "Parches de 60 FPS, cheats y personalización",
                "texto_locucion": "Y número cuatro, Mods exclusivos. Desbloquea 60 FPS y trucos en Walfedw. ¡Escríbenos para catálogo y asesoría!",
                "busqueda_imagen": "PlayStation 4 Console"
            }}
        ],
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
