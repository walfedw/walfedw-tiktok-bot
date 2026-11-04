import os
import json
import google.generativeai as genai

def generar_guion(noticias):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Error: No se encontró la variable GEMINI_API_KEY")

    # Configurar la API oficial de Google AI Studio
    genai.configure(api_key=api_key)

    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el guionista y experto técnico del canal de TikTok @walfedw, especializado en servicio técnico, mantenimiento y novedades de consolas (PS3, PS4, PS5 y Nintendo Switch).

    Aquí tienes las últimas noticias encontradas:
    {texto_noticias}

    INSTRUCCIONES:
    1. Elige LA NOTICIA MÁS INTERESANTE o RELEVANTE sobre firmware, scene, actualizaciones o novedades de consolas.
    2. Si la noticia es un rumor o no está confirmada oficialmente, acláralo usando frases como "se dice que" o "según reportes de la scene". No inventes datos.
    3. Redacta un guion en ESPAÑOL LATINO diseñado para ser leído en un video de 30 a 40 segundos.

    ESTRUCTURA OBLIGATORIA DEL GUION:
    - Gancho (0-3s): Una pregunta o dato impactante para captar atención de inmediato.
    - Explicación (3-25s): Explicar qué pasó o qué significa el término técnico/actualización de forma clara y entretenida. No promocionar descargas o juegos pirateados.
    - Cierre / Llamado a la Acción (25-35s): Invitar al usuario a dejar su consola en tus manos con una frase como: "¿Tienes una PS3, PS4, PS5 o Switch? No te arriesgues, déjala en manos profesionales con nosotros en @walfedw."

    FORMATO DE SALIDA EXACTO (Devuelve ÚNICAMENTE un JSON válido con esta estructura, sin bloques de código ni markdown):
    {{
        "guion": "Texto completo del guion que hablará la voz en off",
        "titulo": "Título llamativo para publicar en TikTok",
        "hashtags": "#PS5 #PS4 #NintendoSwitch #ServicioTecnico #walfedw"
    }}
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    texto_respuesta = response.text.strip()
    if texto_respuesta.startswith("```json"):
        texto_respuesta = texto_respuesta[7:-3].strip()
    elif texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta[3:-3].strip()

    datos = json.loads(texto_respuesta)
    return datos

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print("--- GUION GENERADO ---")
        print(resultado["guion"])
        print("\n--- TÍTULO ---")
        print(resultado["titulo"])
        print("\n--- HASHTAGS ---")
        print(resultado["hashtags"])
