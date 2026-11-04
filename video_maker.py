import asyncio
import textwrap
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip

# Voz en español latino masculina
VOZ_LATINA = "es-MX-DarianNeural"

async def generar_audio(texto, archivo_salida="voz.mp3"):
    communicate = edge_tts.Communicate(texto, VOZ_LATINA)
    await communicate.save(archivo_salida)

def crear_imagen_pantalla(titulo, guion_resumen, ancho=720, alto=1280):
    # Fondo azul oscuro estilizado
    img = Image.new('RGB', (ancho, alto), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    try:
        font_marca = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        font_texto = ImageFont.truetype("DejaVuSans.ttf", 26)
    except:
        font_marca = font_titulo = font_texto = ImageFont.load_default()

    # Encabezado con tu marca
    draw.text((ancho // 2, 120), "@walfedw", fill=(0, 210, 255), anchor="mm", font=font_marca)
    draw.text((ancho // 2, 170), "SERVICIO TÉCNICO DE CONSOLAS", fill=(255, 200, 0), anchor="mm", font=font_texto)

    # Título de la noticia
    lineas_titulo = textwrap.wrap(titulo, width=28)
    y_pos = 320
    for linea in lineas_titulo:
        draw.text((ancho // 2, y_pos), linea, fill=(255, 255, 255), anchor="mm", font=font_titulo)
        y_pos += 42

    # Texto descriptivo/resumen
    lineas_guion = textwrap.wrap(guion_resumen[:220] + "...", width=34)
    y_pos = y_pos + 60
    for linea in lineas_guion:
        draw.text((ancho // 2, y_pos), linea, fill=(210, 220, 240), anchor="mm", font=font_texto)
        y_pos += 36

    # Pie de página (Call to Action)
    draw.rectangle([40, 1080, 680, 1180], fill=(30, 41, 59), outline=(0, 210, 255), width=2)
    draw.text((ancho // 2, 1115), "PS3 • PS4 • PS5 • SWITCH", fill=(255, 255, 255), anchor="mm", font=font_marca)
    draw.text((ancho // 2, 1150), "¡Escríbenos para mantenimiento!", fill=(0, 210, 255), anchor="mm", font=font_texto)

    img.save("fondo_pantalla.png")

def crear_video(guion_texto, titulo_texto, archivo_salida="noticia_tiktok.mp4"):
    print("Generando audio de voz en off...")
    asyncio.run(generar_audio(guion_texto, "voz.mp3"))

    print("Generando plantilla visual...")
    crear_imagen_pantalla(titulo_texto, guion_texto)

    print("Ensamblando video...")
    audio = AudioFileClip("voz.mp3")
    clip = ImageClip("fondo_pantalla.png").set_duration(audio.duration)
    video = clip.set_audio(audio)

    video.write_videofile(
        archivo_salida,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )

    audio.close()
    video.close()
    return archivo_salida

if __name__ == "__main__":
    crear_video(
        "¿Sabías que actualizar tu consola sin revisión previa puede causar sobrecalentamiento? En Walfedw mantenemos tu equipo como nuevo.",
        "Mantenimiento Preventivo de Consolas"
    )
