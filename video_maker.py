import PIL.Image

# Parche de compatibilidad para MoviePy y versiones recientes de Pillow
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import asyncio
import re
import base64
import requests
import edge_tts
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips

VOCES = ["es-MX-DarianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]
URL_BGM_GAMING = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73229.mp3"

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

def obtener_imagen_base64(nombre_juego):
    """Descarga la imagen oficial HD y la convierte a Data URI Base64 para carga 100% garantizada en Playwright."""
    try:
        url_api = f"https://api.rawg.io/api/games?search={requests.utils.quote(nombre_juego)}&key=c53a23720ea1477389822e6e3176477d&page_size=1"
        res = requests.get(url_api, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("results") and data["results"][0].get("background_image"):
                img_url = data["results"][0]["background_image"]
                img_res = requests.get(img_url, timeout=12)
                if img_res.status_code == 200:
                    b64 = base64.b64encode(img_res.content).decode("utf-8")
                    print(f"Imagen HD descargada y convertida a Base64 para: {nombre_juego}")
                    return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        print(f"Advertencia descargando imagen para {nombre_juego}: {e}")
    
    # Imagen de respaldo cyberpunk
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP..."

def descargar_musica_fondo():
    archivo_bgm = "bgm.mp3"
    if os.path.exists(archivo_bgm):
        return archivo_bgm
    try:
        res = requests.get(URL_BGM_GAMING, timeout=15)
        if res.status_code == 200:
            with open(archivo_bgm, "wb") as f:
                f.write(res.content)
            return archivo_bgm
    except Exception as e:
        print(f"No se pudo descargar BGM: {e}")
    return None

def generar_html_escena(titulo_superior, badge_text, titulo_principal, detalle, b64_img, nombre_salida_html):
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, sans-serif; }}
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
            background-image: url('{b64_img}');
            background-size: cover;
            background-position: center;
            filter: brightness(0.50);
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
            background: rgba(15, 23, 42, 0.88);
            border: 2px solid #00d2ff;
            border-radius: 20px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 0 25px rgba(0, 210, 255, 0.5);
            backdrop-filter: blur(12px);
        }}
        .brand {{ font-size: 36px; font-weight: 900; color: #00d2ff; letter-spacing: 2px; text-shadow: 0 0 12px #00d2ff; }}
        .sub-brand {{ font-size: 18px; color: #ffc800; font-weight: 700; margin-top: 4px; }}

        .main-card {{
            background: rgba(15, 23, 42, 0.92);
            border: 2px solid #00d2ff;
            border-radius: 24px;
            padding: 28px 22px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.85);
            backdrop-filter: blur(15px);
            text-align: center;
        }}
        .category-title {{ font-size: 22px; font-weight: 800; color: #a5f3fc; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; }}
        .item-number {{ display: inline-block; background: #00d2ff; color: #0b0f19; font-size: 22px; font-weight: 900; padding: 6px 16px; border-radius: 12px; margin-bottom: 12px; }}
        .item-title {{ font-size: 32px; font-weight: 900; color: #ffffff; text-transform: uppercase; line-height: 1.2; text-shadow: 0 0 12px rgba(0,210,255,0.6); margin-bottom: 10px; }}
        .item-desc {{ font-size: 21px; font-weight: 600; color: #fde047; line-height: 1.35; }}

        .cta-box {{
            background: linear-gradient(135deg, #00d2ff 0%, #0072ff 100%);
            border-radius: 20px;
            padding: 18px;
            text-align: center;
            color: #0b0f19;
            box-shadow: 0 0 30px rgba(0, 210, 255, 0.6);
        }}
        .cta-title {{ font-size: 26px; font-weight: 900; letter-spacing: 1px; }}
        .cta-desc {{ font-size: 18px; font-weight: 800; margin-top: 2px; opacity: 0.95; }}
    </style>
</head>
<body>
    <div class="bg-image"></div>
    <div class="container">
        <div class="header">
            <div class="brand">@WALFEDW</div>
            <div class="sub-brand">CONSOLAS FLASHEADAS - JUEGOS - MANTENIMIENTO</div>
        </div>
        <div class="main-card">
            <div class="category-title">{titulo_superior}</div>
            <div class="item-number">{badge_text}</div>
            <div class="item-title">{titulo_principal}</div>
            <div class="item-desc">{detalle}</div>
        </div>
        <div class="cta-box">
            <div class="cta-title">PS3 - PS4 - PS5 - SWITCH</div>
            <div class="cta-desc">Escribenos para Asesoria y Catalogo</div>
        </div>
    </div>
</body>
</html>"""
    
    with open(nombre_salida_html, "w", encoding="utf-8") as f:
        f.write(html_content)

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

def procesar_escena_individual(idx, sup_title, badge, main_title, detail, locucion, query_img, archivos_temp):
    audio_file = f"voz_{idx}.mp3"
    asyncio.run(generar_audio(locucion, audio_file))
    audio_clip = AudioFileClip(audio_file)
    duracion = audio_clip.duration

    b64_img = obtener_imagen_base64(query_img)

    html_file = f"escena_{idx}.html"
    png_file = f"escena_{idx}.png"
    generar_html_escena(sup_title, badge, main_title, detail, b64_img, html_file)
    renderizar_html_a_png(html_file, png_file)

    clip_base = ImageClip(png_file).set_duration(duracion)
    clip_anim = clip_base.resize(lambda t: 1 + 0.03 * (t / duracion)).set_position(('center', 'center'))

    subs_escena, temp_subs = generar_subtitulos_escena(locucion, duracion)
    video_escena = CompositeVideoClip([clip_anim] + subs_escena, size=(720, 1280)).set_audio(audio_clip)

    archivos_temp.extend([audio_file, html_file, png_file] + temp_subs)
    return video_escena

def crear_video(datos_guion, archivo_salida="noticia_tiktok.mp4"):
    titulo_general = datos_guion.get("titulo_general", "TOP JUEGOS CONSOLA FLASHEADAS")
    gancho_loc = datos_guion.get("gancho_locucion", "¿Tienes tu PS4 flasheada? Guarda estos 4 indispensables.")
    gancho_tit = datos_guion.get("gancho_titulo", "¿PS4 FLASHEADA?")
    escenas = datos_guion.get("escenas", [])
    cierre_loc = datos_guion.get("cierre_locucion", "¿Cuál es tu favorito? Comenta o escríbenos al privado.")
    cierre_tit = datos_guion.get("cierre_titulo", "¿CUÁL ES TU FAVORITO?")

    clips_completos = []
    archivos_temporales = []

    print("1. Renderizando Gancho Inicial...")
    clip_gancho = procesar_escena_individual(
        0, titulo_general, "⚡ ATENCIÓN GAMERS ⚡", gancho_tit, 
        "Guarda estos 4 títulos indispensables ya", gancho_loc, "PlayStation 4 Console", archivos_temporales
    )
    clips_completos.append(clip_gancho)

    print(f"2. Renderizando {len(escenas)} escenas principales...")
    for idx, esc in enumerate(escenas, 1):
        item_nom = esc.get("item", f"Opción #{idx}")
        item_det = esc.get("detalle", "")
        item_loc = esc.get("locucion", "")
        item_q = esc.get("busqueda_imagen", item_nom)

        clip_item = procesar_escena_individual(
            idx, titulo_general, f"OPCIÓN #{idx}", item_nom, 
            item_det, item_loc, item_q, archivos_temporales
        )
        clips_completos.append(clip_item)

    print("3. Renderizando Escena Final de Cierre (CTA)...")
    clip_cierre = procesar_escena_individual(
        99, titulo_general, "💬 RESPONDE EN COMENTARIOS", cierre_tit, 
        "Escríbenos para el catálogo completo", cierre_loc, "PlayStation Gaming Setup", archivos_temporales
    )
    clips_completos.append(clip_cierre)

    print("4. Concatenando video base...")
    video_final = concatenate_videoclips(clips_completos)

    print("5. Mezclando Música de Fondo (BGM)...")
    bgm_path = descargar_musica_fondo()
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm_clip = AudioFileClip(bgm_path)
            total_dur = video_final.duration
            if bgm_clip.duration < total_dur:
                n_loops = int(total_dur / bgm_clip.duration) + 1
                bgm_clip = concatenate_videoclips([bgm_clip] * n_loops)
            bgm_clip = bgm_clip.subclip(0, total_dur).volumex(0.14)
            audio_mezclado = CompositeAudioClip([video_final.audio, bgm_clip])
            video_final = video_final.set_audio(audio_mezclado)
        except Exception as e:
            print(f"Advertencia al mezclar BGM: {e}")

    print("6. Renderizando MP4...")
    video_final.write_videofile(
        archivo_salida,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )

    video_final.close()

    for f in archivos_temporales:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
