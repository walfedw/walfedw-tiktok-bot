import PIL.Image

# Parche de compatibilidad para versiones de MoviePy con Pillow
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
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip

VOCES = ["es-MX-DarianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?@#\-áéíóúÁÉÍÓÚñÑ]', '', texto).strip()

async def generar_audio(texto, archivo_salida="voz.mp3"):
    texto_procesar = limpiar_texto(texto)
    if not texto_procesar:
        texto_procesar = "Flasheo, liberación, juegos y mantenimiento para consolas en Walfedw."

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
        prompt_enc = urllib.parse.quote(prompt_ingles + " gaming console hardware dark neon light 8k")
        return f"https://image.pollinations.ai/prompt/{prompt_enc}?width=720&height=1280&nologo=true&seed=42"
    except:
        return "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=720&h=1280&fit=crop"

def generar_base_html(titulo, codigo_pantalla, prompt_img):
    url_bg = descargar_url_imagen(prompt_img)
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{
            width: 720px;
            height: 1280px;
            background-color: #0b0f19;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 45px 35px;
            position: relative;
            overflow: hidden;
        }}
        .bg-image {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: url('{url_bg}');
            background-size: cover;
            background-position: center;
            filter: blur(10px) brightness(0.30);
            z-index: 1;
        }}
        .container {{
            position: relative;
            z-index: 2;
            display: flex;
            flex-direction: column;
            height: 100%;
            justify-content: space-between;
        }}
        .header {{
            background: rgba(15, 23, 42, 0.80);
            border: 2px solid #00d2ff;
            border-radius: 20px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 0 25px rgba(0, 210, 255, 0.4);
            backdrop-filter: blur(12px);
        }}
        .brand {{ font-size: 38px; font-weight: 900; color: #00d2ff; letter-spacing: 2px; text-shadow: 0 0 12px #00d2ff; }}
        .sub-brand {{ font-size: 19px; color: #ffc800; font-weight: 700; margin-top: 6px; }}

        .main-card {{
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(0, 210, 255, 0.5);
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
            backdrop-filter: blur(15px);
        }}
        .title {{ font-size: 30px; font-weight: 800; color: #ffffff; margin-bottom: 20px; line-height: 1.3; text-transform: uppercase; }}
        
        .code-box {{
            background: #050811;
            border-left: 4px solid #00d2ff;
            border-radius: 10px;
            padding: 16px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 19px;
            color: #a5f3fc;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
        }}

        .subtitles-space {{
            height: 180px;
        }}

        .cta-box {{
            background: linear-gradient(135deg, #00d2ff 0%, #0072ff 100%);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            color: #0b0f19;
            box-shadow: 0 0 30px rgba(0, 210, 255, 0.6);
        }}
        .cta-title {{ font-size: 28px; font-weight: 900; letter-spacing: 1px; }}
        .cta-desc {{ font-size: 19px; font-weight: 800; margin-top: 4px; opacity: 0.95; }}
    </style>
</head>
<body>
    <div class="bg-image"></div>
    <div class="container">
        <div class="header">
            <div class="brand">@WALFEDW</div>
            <div class="sub-brand">⚡ FLASHEO • JUEGOS • SERVICIO TÉCNICO ⚡</div>
        </div>

        <div class="main-card">
            <div class="title">{titulo}</div>
            <div class="code-box">
                <span style="color:#f43f5e">console_status</span> {<br>
                  <span style="color:#38bdf8">mode</span>: <span style="color:#fde047">"HEN / GoldHEN"</span>;<br>
                  <span style="color:#38bdf8">service</span>: <span style="color:#4ade80">"Juegos + Mantenimiento"</span>;<br>
                }
            </div>
        </div>

        <div class="subtitles-space"></div>

        <div class="cta-box">
            <div class="cta-title">PS3 • PS4 • PS5 • SWITCH</div>
            <div class="cta-desc">¡Escríbenos para Asesoría y Catálogo!</div>
        </div>
    </div>
</body>
</html>"""
    
    with open("template.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def renderizar_html_a_imagen():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 720, "height": 1280})
        ruta_absoluta = os.path.abspath("template.html")
        page.goto(f"file://{ruta_absoluta}")
        page.screenshot(path="fondo_pantalla.png")
        browser.close()

def crear_clip_subtitulo(texto_frase, duracion_frase, ancho=720, alto=160):
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([20, 10, ancho - 20, alto - 10], radius=16, fill=(10, 15, 30, 230), outline=(0, 210, 255, 255), width=2)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
    except:
        font = ImageFont.load_default()

    words = texto_frase.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 25:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_offset = (alto - (len(lines) * 36)) // 2
    for line in lines:
        draw.text((ancho // 2 + 2, y_offset + 2), line, fill=(0, 0, 0, 255), anchor="mm", font=font)
        draw.text((ancho // 2, y_offset), line, fill=(255, 230, 0, 255), anchor="mm", font=font)
        y_offset += 36

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
        if len(chunk) >= 5 or p.endswith(('.', '?', '!')):
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
        
        clip, temp_file = crear_clip_subtitulo(frase, duracion_frase)
        clip = clip.set_start(tiempo_actual).set_position(("center", 830))
        
        clips_subtitulos.append(clip)
        archivos_temp.append(temp_file)
        tiempo_actual += duracion_frase

    return clips_subtitulos, archivos_temp

def crear_video(guion_texto, titulo_texto, codigo_pantalla="", prompt_img="gaming console hardware", archivo_salida="noticia_tiktok.mp4"):
    print("1. Generando locución...")
    asyncio.run(generar_audio(guion_texto, "voz.mp3"))

    print("2. Generando render base HTML5/CSS3...")
    generar_base_html(titulo_texto, codigo_pantalla, prompt_img)
    renderizar_html_a_imagen()

    print("3. Generando subtítulos dinámicos sincronizados...")
    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    clip_base = ImageClip("fondo_pantalla.png").set_duration(duracion)
    clip_animado = clip_base.resize(lambda t: 1 + 0.03 * (t / duracion))
    clip_animado = clip_animado.set_position(('center', 'center')).set_duration(duracion)

    clips_sub, archivos_temp = generar_subtitulos_dinamicos(guion_texto, duracion)

    lista_capas = [clip_animado] + clips_sub
    video_final = CompositeVideoClip(lista_capas, size=(720, 1280)).set_audio(audio)

    print("4. Renderizando MP4...")
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

    for f in archivos_temp:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
