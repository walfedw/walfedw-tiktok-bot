import os
import requests
from rss_reader import obtener_noticias
from script_gen import generar_guion
from video_maker import crear_video

def enviar_a_telegram(video_path, titulo, guion, hashtags):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise ValueError("Error: Faltan las credenciales de Telegram.")

    url_video = f"https://api.telegram.org/bot{token}/sendVideo"
    
    # Recortar el guion para garantizar que la descripción no exceda el límite de 1024 caracteres de Telegram
    guion_caption = guion if len(guion) <= 650 else guion[:647] + "..."

    mensaje_caption = (
        f"🎬 *¡NUEVO VIDEO PARA TIKTOK!*\n\n"
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
    print("1. Buscando tendencias en Reddit y blogs de Scene...")
    noticias = obtener_noticias()
    if not noticias:
        print("No se encontraron noticias.")
        return

    print("2. Generando guion enfocado en consolas flasheadas...")
    datos = generar_guion(noticias)

    codigo_pantalla = datos.get("codigo_pantalla", "")
    prompt_imagen = datos.get("image_prompt", "ps4 console hardware neon")

    print("3. Renderizando video con interfaz HTML/CSS...")
    archivo_video = crear_video(
        datos["guion"], 
        datos["titulo"], 
        codigo_pantalla, 
        prompt_imagen
    )

    print("4. Enviando el video a Telegram...")
    enviar_a_telegram(
        archivo_video, 
        datos["titulo"], 
        datos["guion"], 
        datos["hashtags"]
    )
    print("¡Proceso finalizado correctamente!")

if __name__ == "__main__":
    main()
