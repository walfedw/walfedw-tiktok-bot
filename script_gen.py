import json
import time
import requests

def generar_guion(noticias):
    texto_noticias = "\n".join([f"- {n['titulo']}: {n['resumen']}" for n in noticias[:10]])

    prompt = f"""
    Eres el experto técnico del canal @walfedw, especializado en consolas flasheadas/liberadas (PS3, PS4, PS5 y Nintendo Switch).

    Aquí tienes las tendencias extraídas de Reddit y la comunidad Scene:
    {texto_noticias}

    INSTRUCCIONES:
    1. Si hay un tema popular sobre juegos indispensables, exploits de GoldHEN/HEN, emulación o mantenimiento, úsalo.
    2. Si los temas son vagos, genera un guion sobre: "Los mejores juegos indispensables para aprovechar tu PS4 Flasheada" o "Ventajas de flashear PS4 vs Tenerla Normal".
    3. Redacta un guion dinámico en ESPAÑOL LATINO (30-40 segundos) con un gran gancho inicial y llamado a la acción final para adquirir juegos, asesoría o mantenimiento con @walfedw.
    4. Genera una pequeña estructura de texto informativo sobre la consola para mostrarlo en pantalla.

    FORMATO DE SALIDA EXACTO (JSON puro sin markdown):
    {{
        "guion": "Texto completo que dirá la voz en off",
        "titulo": "TOP JUEGOS INDISPENSABLES PS4 FLASHEADA",
        "codigo_pantalla": "HEN 11.00 - GoldHEN Loaded",
        "hashtags": "#PS4Flasheada #JuegosPS4 #GoldHEN #NintendoSwitch #walfedw",
        "image_prompt": "ps4 console cyberpunk glowing neon background photorealistic"
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
