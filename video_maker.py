import asyncio
import textwrap
import re
import urllib.parse
import requests
import edge_tts
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip

VOCES = ["es-MX-DarianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?@#\-áéíóúÁÉÍÓÚñÑ]', '', texto).strip()

async def generar_audio(texto, archivo_salida="voz.mp3"):
    texto_procesar = limpiar_texto(texto)
    if not texto_procesar:
        texto_procesar = "Servicio técnico y mantenimiento profesional para consolas en Walfedw."

    for voz in VOCES:
        try:
            communicate = edge_tts.Communicate(texto_procesar, voz)
            await communicate.save(archivo_salida)
            return
        except Exception as e:
            print(f"Advertencia con voz {voz}: {e}")

    raise RuntimeError("Error al generar el audio.")

def descargar_imagen_fondo(prompt_ingles, ancho=720, alto=1280):
    try:
        prompt_enc = urllib.parse.quote(prompt_ingles + " gaming console hardware high quality photorealistic 8k")
        url_img = f"https://image.pollinations.ai/prompt/{prompt_enc}?width={ancho}&height={alto}&nologo=true&seed=42"
        print(f"Descargando imagen de fondo desde URL: {url_img}")
        res = requests.get(url_img, timeout=20)
        if res.status_code == 200:
            return Image.open(BytesIO(res.content)).convert("RGBA")
    except Exception as e:
        print(f"No se pudo descargar la imagen por URL ({e}), usando fondo por defecto.")
    
    # Fondo de respaldo
    img = Image.new('RGBA', (ancho, alto), color=(15, 23, 42, 255))
    return img

def crear_imagen_pantalla(titulo, guion_resumen, prompt_img="", ancho=720, alto=1280):
    # 1. Obtener imagen base HD de fondo
    bg_img = descargar_imagen_fondo(prompt_img, ancho, alto)
    
    # 2. Aplicar desenfoque artístico para legibilidad
    bg_blurred = bg_img.filter(ImageFilter.GaussianBlur(radius=6))
    
    # 3. Superponer capa de gradiente oscuro semitransparente
    overlay = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Degradado oscuro en la zona media e inferior
    draw_overlay.rectangle([0, 0, ancho, alto], fill=(10, 15, 30, 160))
    draw_overlay.rectangle([30, 260, ancho - 30, 1020], fill=(15, 23, 42, 210), outline=(0, 210, 255, 255), width=2)
    
    # Combinar capas
    img_final = Image.alpha_composite(bg_blurred, overlay).convert('RGB')
    draw = ImageDraw.Draw(img_final)

    try:
        font_marca = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        font_texto = ImageFont.truetype("DejaVuSans.ttf", 25)
        font_badge = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except:
        font_marca = font_titulo = font_texto = font_badge = ImageFont.load_default()

    # Badge superior de marca
    draw.text((ancho // 2, 120), "@WALFEDW", fill=(0, 210, 255), anchor="mm", font=font_marca)
    draw.text((ancho // 2, 165), "⚡ TECH NEWS & SERVICIO TÉCNICO ⚡", fill=(255, 200, 0), anchor="mm", font=font_badge)

    # Título principal de la noticia
    lineas_titulo = textwrap.wrap(titulo, width=26)
    y_pos = 320
    for linea in lineas_titulo:
        draw.text((ancho // 2, y_pos), linea, fill=(255, 255, 255), anchor="mm", font=font_titulo)
        y_pos += 42

    # Línea divisora neón
    draw.line([80, y_pos + 15, ancho - 80, y_pos + 15], fill=(0, 210, 255), width=3)

    # Texto o resumen
    lineas_guion = textwrap.wrap(guion_resumen[:220] + "...", width=32)
    y_pos += 60
    for linea in lineas_guion:
        draw.text((ancho // 2, y_pos), linea, fill=(220, 230, 245), anchor="mm", font=font_texto)
        y_pos += 36

    # Call to Action inferior destacado
    draw.rectangle([40, 1060, ancho - 40, 1180], fill=(0, 210, 255, 255))
    draw.text((ancho // 2, 1095), "PS3 • PS4 • PS5 • SWITCH", fill=(10, 15, 30), anchor="mm", font=font_marca)
    draw.text((ancho // 2, 1140), "Mantenimiento y Reparación Profesional", fill=(10, 15, 30), anchor="mm", font=font_badge)

    img_final.save("fondo_pantalla.png")

def crear_video(guion_texto, titulo_texto, prompt_img="gaming console hardware", archivo_salida="noticia_tiktok.mp4"):
    print("1. Generando locución de voz en off...")
    asyncio.run(generar_audio(guion_texto, "voz.mp3"))

    print("2. Generando composición gráfica profesional...")
    crear_imagen_pantalla(titulo_texto, guion_texto, prompt_img)

    print("3. Renderizando video con animación dinámicos...")
    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    # Crear clip con movimiento sutil de Zoom In (Ken Burns Effect)
    clip_base = ImageClip("fondo_pantalla.png").set_duration(duracion)
    
    # Animación de zoom sutil para darle dinamismo de video
    clip_animado = clip_base.resize(lambda t: 1 + 0.04 * (t / duracion))
    clip_animado = clip_animado.set_position(('center', 'center')).set_duration(duracion)

    video_final = CompositeVideoClip([clip_animado], size=(720, 1280)).set_audio(audio)

    video_final.write_videofile(
        archivo_salida,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )

    audio.close()
    video_final.close()
    return archivo_salida
