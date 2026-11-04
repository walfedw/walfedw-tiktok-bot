import json
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el guionista y experto técnico del canal de TikTok @walfedw, especializado en servicio técnico, mantenimiento y novedades de consolas (PS3, PS4, PS5 y Nintendo Switch).

    Aquí tienes las últimas noticias encontradas:
    {texto_noticias}

    INSTRUCCIONES:
    1. Elige LA NOTICIA MÁS INTERESANTE sobre firmware, scene, actualizaciones o consolas.
    2. Redacta un guion en ESPAÑOL LATINO para un video de 30 a 40 segundos.
    3. Genera una descripción de imagen corta EN INGLÉS para la portada (ej: "PS5 console motherboard repair internal chips dark background neon light photorealistic").

    FORMATO DE SALIDA EXACTO (Devuelve ÚNICAMENTE un JSON válido sin markdown):
    {{
        "guion": "Texto completo del guion que hablará la voz en off",
        "titulo": "Título llamativo para publicar en TikTok",
        "hashtags": "#PS5 #PS4 #NintendoSwitch #ServicioTecnico #walfedw",
        "image_prompt": "descripción breve en inglés sobre la imagen de fondo"
    }}
    """

    print("Generando guion e idea visual...")
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "jsonMode": True
    }

    response = requests.post(url, json=payload, timeout=30)
    texto_respuesta = response.text.strip()

    if "```json" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
    elif "```" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()

    datos = json.loads(texto_respuesta)
    return datos

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
