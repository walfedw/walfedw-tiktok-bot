import json
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico y creador de contenido de @walfedw, canal especializado en:
    - Flasheo, Liberación, Homebrew, HEN, GoldHEN, Atmosphere y Custom Firmwares.
    - Servicio técnico, mantenimiento preventivo y solución de sobrecalentamiento.
    - Comparativas y recomendaciones prácticas (ejemplo: PS4 Liberada vs PS4 Normal, ventajas de flashear PS3/Switch, etc.).
    - Consolas objetivo: PS3, PS4, PS5 y Nintendo Switch.

    Aquí tienes las últimas publicaciones encontradas:
    {texto_noticias}

    INSTRUCCIONES:
    1. Si hay novedades sobre Scene, explotaciones de firmware, actualizaciones o Homebrew en las noticias, úsalas.
    2. Si las noticias son genéricas (como lanzamientos de juegos o rumores de GTA 6), IG NÓRALAS y crea un tema educativo/comercial propio de alta conversión sobre flasheo, liberación, rendimiento o mantenimiento para PS3, PS4, PS5 o Switch.
    3. Redacta un guion en ESPAÑOL LATINO de 30 a 40 segundos con gancho alto, explicación clara y un llamado a la acción final hacia @walfedw para asesoría, juegos y servicio técnico.
    4. Genera un prompt de imagen en INGLÉS enfocado en hardware de consolas, chips, modificación o luces neón.

    FORMATO DE SALIDA EXACTO (Devuelve ÚNICAMENTE un JSON válido sin markdown):
    {{
        "guion": "Texto del guion para la voz en off con llamado a la acción para consultar con @walfedw",
        "titulo": "Título atractivo para TikTok",
        "hashtags": "#PS4Flasheada #PS5 #NintendoSwitch #Homebrew #ServicioTecnico #walfedw",
        "image_prompt": "gaming console motherboard chip modding dark neon lighting hd"
    }}
    """

    print("Generando guion enfocado en Flasheo, Homebrew y Mantenimiento...")
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
