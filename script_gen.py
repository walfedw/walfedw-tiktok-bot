import json
import time
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico y creador de contenido de @walfedw, canal especializado en:
    - Novedades de la Scene/Homebrew (mencionando desarrollos de referentes como NanospeedGamer, TheWizWiki, GoldHEN, HEN, Atmosphere).
    - Flasheo, liberación y Custom Firmwares para PS3, PS4, PS5 y Nintendo Switch.
    - Consejos sobre si conviene una consola liberada vs original, catálogo de juegos y mantenimiento preventivo.

    Aquí tienes las últimas novedades recopiladas:
    {texto_noticias}

    INSTRUCCIONES:
    1. Si hay novedades sobre GoldHEN, exploiteo de PS4/PS5, avances de NanospeedGamer/TheWizWiki o Scene, úsalas como tema principal.
    2. Si los textos recopilados son genéricos, genera un tema educativo/comercial propio sobre ventajas de flashear PS3/PS4/PS5/Switch o comparativas de rendimiento.
    3. Redacta un guion en ESPAÑOL LATINO de 30 a 40 segundos con gancho de alto impacto y llamado a la acción hacia @walfedw para asesoría, juegos y servicio técnico.
    4. Genera un prompt de imagen en INGLÉS enfocado en chips de consolas, luces neón o modificación de hardware.

    FORMATO DE SALIDA EXACTO (Devuelve ÚNICAMENTE un JSON válido sin markdown):
    {{
        "guion": "Texto del guion para la voz en off con llamado a la acción hacia @walfedw",
        "titulo": "Título atractivo para TikTok",
        "hashtags": "#PS4Flasheada #PS5Jailbreak #GoldHEN #NintendoSwitch #ServicioTecnico #walfedw",
        "image_prompt": "gaming console motherboard chip modding dark neon lighting hd"
    }}
    """

    print("Generando guion con reintentos y tolerancia a tiempo de espera...")
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "jsonMode": True
    }

    # Intentar hasta 3 veces con timeout amplio
    for intento in range(1, 4):
        try:
            print(f"Intento {intento} enviando solicitud a la IA...")
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                texto_respuesta = response.text.strip()
                if "```json" in texto_respuesta:
                    texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
                elif "```" in texto_respuesta:
                    texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()

                datos = json.loads(texto_respuesta)
                return datos
        except Exception as e:
            print(f"Advertencia en intento {intento}: {e}")
            time.sleep(3)

    raise RuntimeError("No se pudo obtener respuesta del generador de texto tras 3 intentos.")

if __name__ == "__main__":
    from rss_reader import obtener_noticias
    noticias_prueba = obtener_noticias()
    if noticias_prueba:
        resultado = generar_guion(noticias_prueba)
        print(resultado)
