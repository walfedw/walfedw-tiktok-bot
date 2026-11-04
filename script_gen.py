import json
import time
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico y creador de contenido del canal @walfedw, especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Tendencias actuales de la comunidad:
    {texto_noticias}

    INSTRUCCIONES CLAVE:
    1. PROHIBIDO MENCIONAR VERSIONES NUMÉRICAS DE FIRMWARE (NUNCA digas "11.00", "9.00", "5.05", etc.). Usa siempre términos como "consola flasheada", "consola liberada" o "sistema modificado".
    2. Enfócate en tops de juegos indispensables, ventajas de tener la consola flasheada vs normal, o consejos de almacenamiento y mantenimiento.
    3. Redacta un guion dinámico en ESPAÑOL LATINO de 30 a 40 segundos con gancho de alto impacto y llamado a la acción hacia @walfedw.
    4. Genera una lista corta de 3 a 4 elementos principales que la voz en off mencionará para MOSTRARLOS VISUALMENTE EN PANTALLA.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "guion": "Texto completo que dirá la voz en off hablando de la consola flasheada sin números de versión",
        "titulo": "TOP JUEGOS INDISPENSABLES PS4 FLASHEADA",
        "elementos_pantalla": [
            "The Last of Us Part II",
            "Ghost of Tsushima",
            "God of War Ragnarök",
            "Mods y Trucos Exclusivos"
        ],
        "hashtags": "#PS4Flasheada #JuegosPS4 #NintendoSwitch #ConsolaFlasheada #walfedw",
        "image_prompt": "ps4 console gaming room cyberpunk glowing neon lighting 8k photorealistic"
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
