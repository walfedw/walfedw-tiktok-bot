import PIL.Image

# Parche de compatibilidad para MoviePy y versiones recientes de Pillow
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import asyncio
import re
import urllib.parse
import requests
import edge_tts
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

VOCES = ["es-MX-DarianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?@#\-áéíóúÁÉÍÓÚñÑ]', '', texto).strip()

async def generar_audio(texto, archivo_salida="voz.mp3"):
    texto_procesar = limpiar_texto(texto)
    if not texto_procesar:
        texto_procesar = "Consola flasheada, liberación, juegos y servicio técnico en Walfedw."

    for voz in VOCES:
        try:
            communicate = edge_tts.Communicate(texto_procesar, voz)
            await communicate.save(archivo_salida)
            return
        except Exception as e:
            print(f"Advertencia con voz {voz}: {e}")

    raise RuntimeError("Error al generar el audio.")

def descargar_url_imagen(prompt_ingles):
    try:
        prompt_enc = urllib.parse.quote(prompt_ingles + " 8k high quality photorealistic")
        return f"https://image.pollinations.ai/prompt/{prompt_enc}?width=720&height=1280&nologo=true&seed=42"
    except:
        return "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=720&h=1280&fit=crop"

def generar_html_escena(titulo_general, item_nombre, item_detalle, num_escena, prompt_img, nombre_salida_html):
    url_bg = descargar_url_imagen(prompt_img)
    
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='es'>",
        "<head>",
        "    <meta charset='UTF-8'>",
        "    <style>",
        "        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif; }",
        "        body {",
        "            width: 720px;",
        "            height: 1280px;",
        "            background-color: #0b0f19;",
        "            color: #ffffff;",
        "            display: flex;",
        "            flex-direction: column;",
        "            justify-content: space-between;",
        "            padding: 45px 35px;",
        "            position: relative;",
        "            overflow: hidden;",
        "        }",
        "        .bg-image {",
        "            position: absolute;",
        "            top: 0; left: 0; width: 100%; height: 100%;",
        f"           background-image: url('{url_bg}');",
        "            background-size: cover;",
        "            background-position: center;",
        "            filter: brightness(0.40);",
        "            z-index: 1;",
        "        }",
        "        .container {",
        "            position: relative;",
        "            z-index: 2;",
        "            display: flex;",
        "            flex-direction: column;",
        "            height: 100%;",
        "            justify-content: space-between;",
        "        }",
        "        .header {",
        "            background: rgba(15, 23, 42, 0.85);",
        "            border: 2px solid #00d2ff;",
        "            border-radius: 20px;",
        "            padding: 16px;",
        "            text-align: center;",
        "            box-shadow: 0 0 25px rgba(0, 210, 255, 0.4);",
        "            backdrop-filter: blur(12px);",
        "        }",
        "        .brand { font-size: 36px; font-weight: 900; color: #00d2ff; letter-spacing: 2px; text-shadow: 0 0 12px #00d2ff; }",
        "        .sub-brand { font-size: 18px; color: #ffc800; font-weight: 700; margin-top: 4px; }",
        
        "        .main-card {",
        "            background: rgba(15, 23, 42, 0.90);",
        "            border: 2px solid #00d2ff;",
        "            border-radius: 24px;",
        "            padding: 30px 24px;",
        "            box-shadow: 0 15px 35px rgba(0,0,0,0.8);",
        "            backdrop-filter: blur(15px);",
        "            text-align: center;",
        "        }",
        "        .category-title { font-size: 24px; font-weight: 800; color: #a5f3fc; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px; }",
        "        .item-number { display: inline-block; background: #00d2ff; color: #0b0f19; font-size: 22px; font-weight: 900; padding: 6px 16px; border-radius: 12px; margin-bottom: 15px; }",
        "        .item-title { font-size: 34px; font-weight: 900; color: #ffffff; text-transform: uppercase; line-height: 1.2; text-shadow: 0 0 10px rgba(0,210,255,0.5); margin-bottom: 12px; }",
        "        .item-desc { font-size: 22px; font-weight: 600; color: #fde047; line-height: 1.4; }",

        "        .cta-box {",
        "            background: linear-gradient(135deg, #00d2ff 0%, #0072ff 100%);",
        "            border-radius: 20px;",
        "            padding: 18px;",
        "            text-align: center;",
        "            color: #0b0f19;",
        "            box-shadow: 0 0 30px rgba(0, 210, 255, 0.6);",
        "        }",
        "        .cta-title { font-size: 26px; font-weight: 900; letter-spacing: 1px; }",
        "        .cta-desc { font-size: 18px; font-weight: 800; margin-top: 2px; opacity: 0.95; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class='bg-image'></div>",
        "    <div class='container'>",
        "        <div class='header'>",
        "            <div class='brand'>@WALFEDW</div>",
        "            <div class='sub-brand'>CONSOLAS FLASHEADAS - JUEGOS - MANTENIMIENTO</div>",
        "        </div>",
        "        <div class='main-card'>",
        f"           <div class='category-title'>{titulo_general}</div>",
        f"           <div class='item-number'>OPCIÓN #{num_escena}</div>",
        f"           <div class='item-title'>{item_nombre}</div>",
        f"           <div class='item-desc'>{item_detalle}</div>",
        "        </div>",
        "        <div class='cta-box'>",
        "            <div class='cta-title'>PS3 - PS4 - PS5 - SWITCH</div>",
        "            <div class='cta-desc'>Escribenos para Asesoria y Catalogo</div>",
        "        </div>",
        "    </div>",
        "</body>",
        "</html>"
    ]
    
    with open(nombre_salida_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

def renderizar_html_a_png(archivo_html, archivo_png):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 720, "height": 1280})
        ruta_absoluta = os.path.abspath(archivo_html)
        page.goto(f"file://{ruta_absoluta}")
        page.screenshot(path=archivo_png)
        browser.close()

def crear_clip_subtitulo_limpio(texto_frase, duracion_frase, ancho=720, alto=160):
    # Genera subtítulo flotante transparente SIN cajas grandes
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except:
        font = ImageFont.load_default()

    words = texto_frase.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 22:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_offset = (alto - (len(lines) * 40)) // 2
    for line in lines:
        # Borde negro grueso alrededor del texto para máxima legibilidad
        for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3), (-3,0), (3,0), (0,-3), (0,3)]:
            draw.text((ancho // 2 + dx, y_offset + dy), line, fill=(0, 0, 0, 255), anchor="mm", font=font)
        # Texto principal amarillo neón
        draw.text((ancho // 2, y_offset), line, fill=(255, 235, 0, 255), anchor="mm", font=font)
        y_offset += 40

    nombre_temp = f"sub_{abs(hash(texto_frase))}.png"
    img.save(nombre_temp)
    
    clip = ImageClip(nombre_temp).set_duration(duracion_frase)
    return clip, nombre_temp

def generar_subtitulos_dinamicos(guion_texto, duracion_total):
    palabras = guion_texto.split()
    frases = []
    chunk = []
    
    for p in palabras:
        chunk.append(p)
        if len(chunk) >= 4 or p.endswith(('.', '?', '!')):
            frases.append(" ".join(chunk))
            chunk = []
    if chunk:
        frases.append(" ".join(chunk))

    if not frases:
        return [], []

    total_chars = sum(len(f) for f in frases)
    clips_subtitulos = []
    archivos_temp = []
    tiempo_actual = 0.0

    for frase in frases:
        proporcion = len(frase) / total_chars
        duracion_frase = duracion_total * proporcion
        
        clip, temp_file = crear_clip_subtitulo_limpio(frase, duracion_frase)
        # Posición flotante limpia en la zona inferior libre
        clip = clip.set_start(tiempo_actual).set_position(("center", 900))
        
        clips_subtitulos.append(clip)
        archivos_temp.append(temp_file)
        tiempo_actual += duracion_frase

    return clips_subtitulos, archivos_temp

def crear_video(guion_texto, titulo_general, escenas=[], archivo_salida="noticia_tiktok.mp4"):
    print("1. Generando voz en off...")
    asyncio.run(generar_audio(guion_texto, "voz.mp3"))

    audio = AudioFileClip("voz.mp3")
    duracion_total = audio.duration

    if not escenas:
        escenas = [
            {"item": "Consolas Liberadas", "detalle": "Catálogo completo de juegos", "image_prompt": "ps4 console neon"},
            {"item": "Servicio Técnico", "detalle": "Mantenimiento profesional", "image_prompt": "tech repair motherboard"}
        ]

    num_escenas = len(escenas)
    duracion_por_escena = duracion_total / num_escenas

    print(f"2. Generando {num_escenas} escenas visuales con imágenes específicas...")
    clips_escenas = []
    archivos_escenas_temp = []

    for idx, esc in enumerate(escenas, 1):
        html_filename = f"escena_{idx}.html"
        png_filename = f"escena_{idx}.png"
        
        generar_html_escena(
            titulo_general, 
            esc.get("item", f"Opción #{idx}"), 
            esc.get("detalle", ""), 
            idx, 
            esc.get("image_prompt", "gaming console"), 
            html_filename
        )
        renderizar_html_a_png(html_filename, png_filename)
        
        # Clip de imagen con leve zoom
        clip_img = ImageClip(png_filename).set_duration(duracion_por_escena)
        clip_anim = clip_img.resize(lambda t: 1 + 0.03 * (t / duracion_por_escena)).set_position(('center', 'center'))
        
        clips_escenas.append(clip_anim)
        archivos_escenas_temp.extend([html_filename, png_filename])

    # Concatenar todas las escenas para formar la secuencia completa
    video_base = concatenate_videoclips(clips_escenas)

    print("3. Aplicando subtítulos flotantes limpios estilo TikTok...")
    clips_sub, archivos_sub_temp = generar_subtitulos_dinamicos(guion_texto, duracion_total)

    lista_capas = [video_base] + clips_sub
    video_final = CompositeVideoClip(lista_capas, size=(720, 1280)).set_audio(audio)

    print("4. Renderizando video final MP4...")
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

    # Limpieza de archivos temporales
    for f in archivos_escenas_temp + archivos_sub_temp:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
