import PIL.Image

# Parche de compatibilidad para versiones de MoviePy con Pillow
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

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
        texto_procesar = "Flasheo, liberación, juegos y mantenimiento técnico para consolas en Walfedw."

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
            img = Image.open(BytesIO(res.content)).convert("RGBA")
            return img.resize((ancho, alto))
    except Exception as e:
        print(f"Usando fondo por defecto ({e}).")
    
    return Image.new('RGBA', (ancho, alto), color=(15, 23, 42, 255))

def crear_imagen_pantalla(titulo, guion_resumen, prompt_img="", ancho=720, alto=1280):
    bg_img = descargar_imagen_fondo(prompt_img, ancho, alto)
    bg_blurred = bg_img.filter(ImageFilter.GaussianBlur(radius=6))
    
    overlay = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    draw_overlay.rectangle([0, 0, ancho, alto], fill=(10, 15, 30, 160))
    draw_overlay.rectangle([30, 260, ancho - 30, 1020], fill=(15, 23, 42, 210), outline=(0, 210, 255, 255), width=2)
    
    img_final = Image.alpha_composite(bg_blurred, overlay).convert('RGB')
    draw = ImageDraw.Draw(img_final)

    try:
        font_marca = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        font_texto = ImageFont.truetype("DejaVuSans.ttf", 25)
        font_badge = ImageFont.truetype("DejaVuSans-Bold.ttf", 21)
    except:
        font_marca = font_titulo = font_texto = font_badge = ImageFont.load_default()

    # Encabezado principal de Marca
    draw.text((ancho // 2, 120), "@WALFEDW", fill=(0, 210, 255), anchor="mm", font=font_marca)
    draw.text((ancho // 2, 165), "⚡ FLASHEO • JUEGOS • MANTENIMIENTO ⚡", fill=(255, 200, 0), anchor="mm", font=font_badge)

    # Título del tema
    lineas_titulo = textwrap.wrap(titulo, width=28)
    y_pos = 320
    for linea in lineas_titulo:
        draw.text((ancho // 2, y_pos), linea, fill=(255, 255, 255), anchor="mm", font=font_titulo)
        y_pos += 40

    # Separador Neón
    draw.line([80, y_pos + 15, ancho - 80, y_pos + 15], fill=(0, 210, 255), width=3)

    # Resumen / Explicación
    lineas_guion = textwrap.wrap(guion_resumen[:220] + "...", width=32)
    y_pos += 60
    for linea in lineas_guion:
        draw.text((ancho // 2, y_pos), linea, fill=(220, 230, 245), anchor="mm", font=font_texto)
        y_pos += 36

    # Call To Action permanente inferior
    draw.rectangle([40, 1060, ancho - 40, 1180], fill=(0, 210, 255, 255))
    draw.text((ancho // 2, 1095), "PS3 • PS4 • PS5 • SWITCH", fill=(10, 15, 30), anchor="mm", font=font_marca)
    draw.text((ancho // 2, 1140), "¡Servicio Técnico y Liberación de Consolas!", fill=(10, 15, 30), anchor="mm", font=font_badge)

    img_final.save("fondo_pantalla.png")

def crear_video(guion_texto, titulo_texto, prompt_img="gaming console hardware", archivo_salida="noticia_tiktok.mp4"):
    print("1. Generando locución de voz en off...")
    asyncio.run(generar_audio(guion_texto, "voz.mp3"))

    print("2. Generando composición gráfica...")
    crear_imagen_pantalla(titulo_texto, guion_texto, prompt_img)

    print("3. Renderizando video...")
    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    clip_base = ImageClip("fondo_pantalla.png").set_duration(duracion)
    
    # Efecto Zoom In
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
