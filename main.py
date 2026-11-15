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
    mensaje_caption = (
        f"🔥 *¡NUEVO TIKTOK VIRAL (WALFEDW SERVICES)!*\n\n"
        f"📌 *Enfoque:* {titulo}\n\n"
        f"🎙️ *Guion:*\n{guion_completo}\n\n"
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
    print("1. Consultando novedades de la Scene...")
    noticias = obtener_noticias() or []

    print("2. Generando guion viral corto para Walfedw Services...")
    datos = generar_guion(noticias)

    print("3. Renderizando video con cortes rápidos, subtítulos CapCut y flyer...")
    archivo_video = crear_video(datos)

    print("4. Enviando a Telegram...")
    enviar_a_telegram(
        archivo_video,
        datos.get("titulo_general", "Flasheo PS3 • PS4 • PS5"),
        datos.get("locucion_completa", ""),
        datos.get("hashtags", "#PS4Flasheada #Walfedw")
    )
    print("¡Listo!")

if __name__ == "__main__":
    main()
