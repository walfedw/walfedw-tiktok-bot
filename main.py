import os
import requests
from rss_reader import obtener_noticias
from script_gen import generar_guion
from video_maker import crear_video

def enviar_a_telegram(video_path, titulo, guion_completo, hashtags):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Error: Faltan las credenciales de Telegram.")

    url_video = f"https://api.telegram.org/bot{token}/sendVideo"
    
    guion_caption = guion_completo if len(guion_completo) <= 650 else guion_completo[:647] + "..."

    mensaje_caption = (
        f"🎬 *¡NUEVO VIDEO PARA TIKTOK (PS4)!*\n\n"
        f"📌 *Título:* {titulo}\n\n"
        f"📝 *Guion:*\n{guion_caption}\n\n"
        f"🏷️ *Hashtags:*\n{hashtags}"
    )

    with open(video_path, 'rb') as video_file:
        payload = {
            'chat_id': chat_id,
            'caption': mensaje_caption,
            'parse_mode': 'Markdown'
        }
        files = {'video': video_file}
        response = requests.post(url_video, data=payload, files=files)
    
    if response.status_code == 200:
        print("Video enviado exitosamente a Telegram.")
    else:
        raise RuntimeError(f"Error al enviar a Telegram ({response.status_code}): {response.text}")

def main():
    print("1. Buscando tendencias en Reddit y blogs de Scene PS4...")
    noticias = obtener_noticias()
    if not noticias:
        print("No se encontraron noticias.")
        return

    print("2. Generando guion enfocado exclusivamente en Flasheo de PS4...")
    datos = generar_guion(noticias)

    escenas = datos.get("escenas", [])
    texto_completo = f"{datos.get('gancho_locucion', '')} " + " ".join([e.get("locucion", "") for e in escenas]) + f" {datos.get('cierre_locucion', '')}"

    print("3. Renderizando video optimizado con marco visual de 440px...")
    archivo_video = crear_video(datos)

    print("4. Enviando el video a Telegram...")
    enviar_a_telegram(
        archivo_video, 
        datos.get("titulo_general", "FLASHEO Y JUEGOS PS4"), 
        texto_completo, 
        datos.get("hashtags", "#PS4Flasheada #walfedw")
    )
    print("¡Proceso finalizado correctamente!")

if __name__ == "__main__":
    main()
