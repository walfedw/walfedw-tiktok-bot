import json
import time
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico del canal @walfedw especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Novedades recopiladas:
    {texto_noticias}

    INSTRUCCIONES CLAVE:
    1. PROHIBIDO MENCIONAR NÚMEROS DE FIRMWARE (NUNCA digas "11.00", "9.00", etc.). Usa siempre "consola flasheada" o "sistema liberado".
    2. Crea un contenido dinámico enfocado en TOPS DE JUEGOS INDISPENSABLES o CONSEJOS ÚTILES para consolas liberadas.
    3. Estructura la salida en 4 ESCENAS VISUALES. Cada escena debe tener su título de juego/tema, un texto descriptivo breve y una frase clave en inglés para buscar su imagen de fondo representativa.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "guion": "Texto completo fluido que hablará la voz en off durante todo el video",
        "titulo_general": "TOP JUEGOS INDISPENSABLES PS4 FLASHEADA",
        "escenas": [
            {{
                "item": "The Last of Us Part II",
                "detalle": "Gráficos al máximo y rendimiento superior",
                "image_prompt": "the last of us part 2 game artwork 8k photorealistic"
            }},
            {{
                "item": "Ghost of Tsushima",
                "detalle": "Mundo abierto fluidez total y respuesta rápida",
                "image_prompt": "ghost of tsushima samurai gameplay wallpaper 8k"
            }},
            {{
                "item": "God of War Ragnarök",
                "detalle": "La experiencia completa de Kratos sin límites",
                "image_prompt": "god of war ragnarok kratos epic gaming background 8k"
            }},
            {{
                "item": "Mods y Trucos Exclusivos",
                "detalle": "Mejoras de FPS, cheats y parches personalizados",
                "image_prompt": "cyberpunk ps4 console modding neon light 8k"
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
