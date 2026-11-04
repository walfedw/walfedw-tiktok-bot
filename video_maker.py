import PIL.Image

# Parche de compatibilidad para MoviePy y versiones recientes de Pillow
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import asyncio
import re
import requests
import edge_tts
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

VOCES = ["es-MX-DarianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?@#\-áéíóúÁÉÍÓÚñÑ]', '', texto).strip()

async def generar_audio(texto, archivo_salida):
    texto_procesar = limpiar_texto(texto)
    if not texto_procesar:
        texto_procesar = "Consola flasheada y servicio técnico profesional en Walfedw."

    for voz in VOCES:
        try:
            communicate = edge_tts.Communicate(texto_procesar, voz)
            await communicate.save(archivo_salida)
            return
        except Exception as e:
            print(f"Advertencia con voz {voz}: {e}")

    raise RuntimeError("Error al generar el audio.")

def obtener_imagen_real_juego(nombre_juego):
    """Busca y extrae la URL de la imagen HD oficial del juego en RAWG Games Database."""
    try:
        url_api = f"https://api.rawg.io/api/games?search={requests.utils.quote(nombre_juego)}&key=c53a23720ea1477389822e6e3176477d&page_size=1"
        res = requests.get(url_api, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("results") and data["results"][0].get("background_image"):
                img_url = data["results"][0]["background_image"]
                print(f"Imagen real encontrada para '{nombre_juego}': {img_url}")
                return img_url
    except Exception as e:
        print(f"Error al buscar imagen en RAWG para {nombre_juego}: {e}")
    
    # Imagen de respaldo de alta calidad en caso de fallo
    return "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=1080&h=1920&fit=crop"

def generar_html_escena(titulo_general, item_nombre, item_detalle, num_escena, url_bg, nombre_salida_html):
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
        "            filter: brightness(0.45);",
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
        "            box-shadow: 0 0 25px rgba(0, 210, 255, 0.5);",
        "            backdrop-filter: blur(12px);",
        "        }",
        "        .brand { font-size: 36px; font-weight: 900; color: #00d2ff; letter-spacing: 2px; text-shadow: 0 0 12px #00d2ff; }",
        "        .sub-brand { font-size: 18px; color: #ffc800; font-weight: 700; margin-top: 4px; }",
        
        "        .main-card {",
        "            background: rgba(15, 23, 42, 0.90);",
        "            border: 2px solid #00d2ff;",
        "            border-radius: 24px;",
        "            padding: 28px 22px;",
        "            box-shadow: 0 15px 35px rgba(0,0,0,0.8);",
        "            backdrop-filter: blur(15px);",
        "            text-align: center;",
        "        }",
        "        .category-title { font-size: 22px; font-weight: 800; color: #a5f3fc; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; }",
        "        .item-number { display: inline-block; background: #00d2ff; color: #0b0f19; font-size: 22px; font-weight: 900; padding: 6px 16px; border-radius: 12px; margin-bottom: 12px; }",
        "        .item-title { font-size: 32px; font-weight: 900; color: #ffffff; text-transform: uppercase; line-height: 1.2; text-shadow: 0 0 12px rgba(0,210,255,0.6); margin-bottom: 10px; }",
        "        .item-desc { font-size: 21px; font-weight: 600; color: #fde047; line-height: 1.35; }",

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
        for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3), (-3,0), (3,0), (0,-3), (0,3)]:
            draw.text((ancho // 2 + dx, y_offset + dy), line, fill=(0, 0, 0, 255), anchor="mm", font=font)
        draw.text((ancho // 2, y_offset), line, fill=(255, 235, 0, 255), anchor="mm", font=font)
        y_offset += 40

    nombre_temp = f"sub_{abs(hash(texto_frase))}.png"
    img.save(nombre_temp)
    
    clip = ImageClip(nombre_temp).set_duration(duracion_frase)
    return clip, nombre_temp

def generar_subtitulos_escena(texto_escena, duracion_escena):
    palabras = texto_escena.split()
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
        duracion_frase = duracion_escena * proporcion
        
        clip, temp_file = crear_clip_subtitulo_limpio(frase, duracion_frase)
        clip = clip.set_start(tiempo_actual).set_position(("center", 900))
        
        clips_subtitulos.append(clip)
        archivos_temp.append(temp_file)
        tiempo_actual += duracion_frase

    return clips_subtitulos, archivos_temp

def crear_video(datos_guion, archivo_salida="noticia_tiktok.mp4"):
    titulo_general = datos_guion.get("titulo_general", "TOP JUEGOS CONSOLA FLASHEADAS")
    escenas = datos_guion.get("escenas", [])

    print(f"1. Procesando {len(escenas)} escenas con sincronización e imágenes reales HD...")
    
    clips_completos_escenas = []
    archivos_temporales = []

    for idx, esc in enumerate(escenas, 1):
        item_nombre = esc.get("item", f"Opción #{idx}")
        item_detalle = esc.get("detalle", "")
        texto_locucion = esc.get("texto_locucion", "")
        busqueda_img = esc.get("busqueda_imagen", item_nombre)

        # 1. Generar audio específico para esta escena
        audio_file = f"voz_{idx}.mp3"
        asyncio.run(generar_audio(texto_locucion, audio_file))
        audio_clip = AudioFileClip(audio_file)
        duracion_escena = audio_clip.duration

        # 2. Obtener imagen real del juego desde la API
        url_imagen_real = obtener_imagen_real_juego(busqueda_img)

        # 3. Renderizar imagen HTML
        html_file = f"escena_{idx}.html"
        png_file = f"escena_{idx}.png"
        generar_html_escena(titulo_general, item_nombre, item_detalle, idx, url_imagen_real, html_file)
        renderizar_html_a_png(html_file, png_file)

        # 4. Crear clip visual con animación Ken Burns
        clip_base = ImageClip(png_file).set_duration(duracion_escena)
        clip_anim = clip_base.resize(lambda t: 1 + 0.03 * (t / duracion_escena)).set_position(('center', 'center'))

        # 5. Generar subtítulos sincronizados para esta escena
        subs_escena, temp_subs = generar_subtitulos_escena(texto_locucion, duracion_escena)

        # 6. Combinar video + audio + subtítulos de la escena
        video_escena = CompositeVideoClip([clip_anim] + subs_escena, size=(720, 1280)).set_audio(audio_clip)
        clips_completos_escenas.append(video_escena)

        archivos_temporales.extend([audio_file, html_file, png_file] + temp_subs)

    print("2. Concatenando todas las escenas sincronizadas...")
    video_final = concatenate_videoclips(clips_completos_escenas)

    print("3. Renderizando archivo MP4...")
    video_final.write_videofile(
        archivo_salida,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )

    video_final.close()

    # Limpiar archivos temporales
    for f in archivos_temporales:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
