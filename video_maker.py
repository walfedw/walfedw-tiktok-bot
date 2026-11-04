import PIL.Image

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

# Repositorio 1: Mapa directo HD con imágenes estrictamente verificadas (0 fotos de PS5)
IMAGENES_DIRECTAS = {
    "the last of us part ii": "https://images.rawg.io/media/games/054/05494357022e399589d81d269fd4cb56.jpg",
    "the last of us part 2": "https://images.rawg.io/media/games/054/05494357022e399589d81d269fd4cb56.jpg",
    "marvel's spider-man": "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg",
    "marvels spider-man": "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg",
    "spider-man ps4": "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg",
    "god of war ragnarok": "https://cdn.akamai.steamstatic.com/steam/apps/2322010/header.jpg",
    "god of war ragnarök": "https://cdn.akamai.steamstatic.com/steam/apps/2322010/header.jpg",
    "ghost of tsushima": "https://cdn.akamai.steamstatic.com/steam/apps/2215430/header.jpg",
    "red dead redemption 2": "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg",
    "grand theft auto v": "https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg",
    "gta v": "https://cdn.akamai.steamstatic.com/steam/apps/271590/header.jpg",
    "elden ring": "https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg",
    "bloodborne": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1080&h=1920&fit=crop",
    "resident evil 4 remake": "https://cdn.akamai.steamstatic.com/steam/apps/2050650/header.jpg",
    "playstation 4 dualshock controller": "https://images.unsplash.com/photo-1507457379470-08b800bebc67?w=1080&h=1920&fit=crop",
    "playstation 4 console": "https://images.unsplash.com/photo-1507457379470-08b800bebc67?w=1080&h=1920&fit=crop",
    "servicio flasheo ps4": "https://images.unsplash.com/photo-1507457379470-08b800bebc67?w=1080&h=1920&fit=crop"
}

# Fotos de respaldo 100% PS4 (Mando DualShock 4 negro / ambiente gaming)
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1507457379470-08b800bebc67?w=1080&h=1920&fit=crop",
    "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=1080&h=1920&fit=crop",
    "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1080&h=1920&fit=crop"
]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?@#\-áéíóúÁÉÍÓÚñÑ]', '', texto).strip()

def cargar_logo_base64():
    posibles_nombres = ["walfedw.jpg", "walfedw.png", "logo.jpg", "logo.png"]
    for nombre in posibles_nombres:
        if os.path.exists(nombre):
            try:
                with open(nombre, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                    mime = "image/png" if nombre.endswith(".png") else "image/jpeg"
                    return f"data:{mime};base64,{b64}"
            except Exception as e:
                print(f"Error al procesar logo {nombre}: {e}")
    return ""

async def generar_audio(texto, archivo_salida):
    texto_procesar = limpiar_texto(texto)
    if not texto_procesar:
        texto_procesar = "Flasheo de PS4, catálogo de juegos y software en Walfedw."

    for voz in VOCES:
        try:
            communicate = edge_tts.Communicate(texto_procesar, voz)
            await communicate.save(archivo_salida)
            return
        except Exception as e:
            print(f"Advertencia con voz {voz}: {e}")

    raise RuntimeError("Error al generar el audio.")

def descargar_bytes_a_base64(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    res = requests.get(url, headers=headers, timeout=12)
    if res.status_code == 200 and len(res.content) > 3000:
        b64 = base64.b64encode(res.content).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    raise ValueError("Respuesta inválida al descargar imagen.")

def obtener_imagen_base64(nombre_juego, idx_escena=0):
    nombre_lower = nombre_juego.lower().strip()

    # Repositorio 1: Mapa directo verificado
    for clave, url_directa in IMAGENES_DIRECTAS.items():
        if clave in nombre_lower:
            try:
                print(f"[Mapa Directo HD] Imagen para: '{nombre_juego}'")
                return descargar_bytes_a_base64(url_directa)
            except Exception as e:
                print(f"[Mapa Directo Error] {e}")

    # Repositorio 2: Steam Store API CDN
    try:
        url_steam = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(nombre_juego)}&l=english&cc=US"
        res = requests.get(url_steam, timeout=7, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            data = res.json()
            if data.get("items"):
                app_id = data["items"][0]["id"]
                url_hero = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_hero.jpg"
                url_header = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                for img_test in [url_hero, url_header]:
                    try:
                        print(f"[Steam Store CDN] Imagen para: '{nombre_juego}' (AppID {app_id})")
                        return descargar_bytes_a_base64(img_test)
                    except:
                        continue
    except Exception as e:
        print(f"[Steam API Error] {e}")

    fallback_url = FALLBACK_IMAGES[idx_escena % len(FALLBACK_IMAGES)]
    print(f"[Fallback PS4 HD] Fondo para escena #{idx_escena}")
    return descargar_bytes_a_base64(fallback_url)

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
    logo_b64 = cargar_logo_base64()
    avatar_html = f"<img src='{logo_b64}' class='brand-avatar' />" if logo_b64 else ""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{
            width: 720px;
            height: 1280px;
            background-color: #060911;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 35px 25px;
            position: relative;
            overflow: hidden;
        }}
        .bg-image {{
            position: absolute;
            top: -5%; left: -5%; width: 110%; height: 110%;
            background-image: url('{b64_img}');
            background-size: cover;
            background-position: center;
            filter: blur(30px) brightness(0.30);
            z-index: 1;
            transform: scale(1.08);
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
            background: rgba(15, 23, 42, 0.94);
            border: 2px solid #00d2ff;
            border-radius: 20px;
            padding: 14px 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            box-shadow: 0 0 25px rgba(0, 210, 255, 0.6);
            backdrop-filter: blur(12px);
        }}
        .brand-avatar {{
            width: 65px;
            height: 65px;
            border-radius: 50%;
            border: 2px solid #00d2ff;
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.8);
            object-fit: cover;
        }}
        .header-info {{ text-align: left; }}
        .brand {{ font-size: 34px; font-weight: 900; color: #00d2ff; letter-spacing: 2px; text-shadow: 0 0 12px #00d2ff; line-height: 1; }}
        .sub-brand {{ font-size: 16px; color: #ffc800; font-weight: 800; margin-top: 4px; letter-spacing: 1px; }}

        .main-card {{
            background: rgba(15, 23, 42, 0.95);
            border: 2px solid #00d2ff;
            border-radius: 24px;
            padding: 22px 18px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.9);
            backdrop-filter: blur(15px);
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .category-title {{ font-size: 22px; font-weight: 800; color: #a5f3fc; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }}
        .item-number {{ display: inline-block; background: #00d2ff; color: #0b0f19; font-size: 21px; font-weight: 900; padding: 5px 16px; border-radius: 10px; margin-bottom: 12px; }}

        /* CONTENEDOR VISUAL HD CENTRADO */
        .game-banner-box {{
            width: 100%;
            height: 420px;
            border-radius: 18px;
            overflow: hidden;
            border: 3px solid #00d2ff;
            box-shadow: 0 0 25px rgba(0, 210, 255, 0.5);
            background: #020617;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .game-banner-img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
        }}

        /* LETRAS GRANDES Y LEGIBLES PARA PANTALLA DE CELULAR */
        .item-title {{ font-size: 34px; font-weight: 900; color: #ffffff; text-transform: uppercase; line-height: 1.15; text-shadow: 0 0 14px rgba(0,210,255,0.7); margin-bottom: 8px; }}
        .item-desc {{ font-size: 22px; font-weight: 700; color: #ffe600; line-height: 1.3; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }}

        .cta-box {{
            background: linear-gradient(135deg, #00d2ff 0%, #0072ff 100%);
            border-radius: 20px;
            padding: 18px;
            text-align: center;
            color: #0b0f19;
            box-shadow: 0 0 30px rgba(0, 210, 255, 0.7);
        }}
        .cta-title {{ font-size: 27px; font-weight: 900; letter-spacing: 1px; }}
        .cta-desc {{ font-size: 19px; font-weight: 800; margin-top: 2px; opacity: 0.95; }}
    </style>
</head>
<body>
    <div class="bg-image"></div>
    <div class="container">
        <div class="header">
            {avatar_html}
            <div class="header-info">
                <div class="brand">@WALFEDW</div>
                <div class="sub-brand">FLASHEO • JUEGOS • SOFTWARE</div>
            </div>
        </div>
        <div class="main-card">
            <div class="category-title">{titulo_superior}</div>
            <div class="item-number">{badge_text}</div>
            <div class="game-banner-box">
                <img src="{b64_img}" class="game-banner-img" />
            </div>
            <div class="item-title">{titulo_principal}</div>
            <div class="item-desc">{detalle}</div>
        </div>
        <div class="cta-box">
            <div class="cta-title">PS3 • PS4 • PS5</div>
            <div class="cta-desc">Escribenos para Asesoria y Catalogo de Juegos</div>
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

def crear_clip_subtitulo_limpio(texto_frase, duracion_frase, ancho=720, alto=180):
    img = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
    except:
        font = ImageFont.load_default()

    words = texto_frase.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 18:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_offset = (alto - (len(lines) * 44)) // 2
    for line in lines:
        for dx, dy in [(-4,-4), (4,-4), (-4,4), (4,4), (-4,0), (4,0), (0,-4), (0,4)]:
            draw.text((ancho // 2 + dx, y_offset + dy), line, fill=(0, 0, 0, 255), anchor="mm", font=font)
        draw.text((ancho // 2, y_offset), line, fill=(255, 230, 0, 255), anchor="mm", font=font)
        y_offset += 44

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
        clip = clip.set_start(tiempo_actual).set_position(("center", 920))
        
        clips_subtitulos.append(clip)
        archivos_temp.append(temp_file)
        tiempo_actual += duracion_frase

    return clips_subtitulos, archivos_temp

def procesar_escena_individual(idx, sup_title, badge, main_title, detail, locucion, query_img, archivos_temp):
    audio_file = f"voz_{idx}.mp3"
    asyncio.run(generar_audio(locucion, audio_file))
    audio_clip = AudioFileClip(audio_file)
    duracion = audio_clip.duration

    b64_img = obtener_imagen_base64(query_img, idx)

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
    titulo_general = datos_guion.get("titulo_general", "FLASHEO Y JUEGOS PS4")
    gancho_loc = datos_guion.get("gancho_locucion", "¿Tienes tu PS4 sin flashear? En Walfedw la liberamos hoy.")
    gancho_tit = datos_guion.get("gancho_titulo", "¿TIENES TU PS4 SIN FLASHEAR?")
    escenas = datos_guion.get("escenas", [])
    cierre_loc = datos_guion.get("cierre_locucion", "¿Qué esperas para liberar tu PS4? Escríbenos al privado.")
    cierre_tit = datos_guion.get("cierre_titulo", "¡FLASHEA TU PS4 HOY!")

    clips_completos = []
    archivos_temporales = []

    print("1. Renderizando Gancho Inicial...")
    clip_gancho = procesar_escena_individual(
        0, titulo_general, "⚡ ATENCIÓN GAMERS PS4 ⚡", gancho_tit, 
        "Flasheo profesional y carga de catálogo completo", gancho_loc, "playstation 4 dualshock controller", archivos_temporales
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
        99, titulo_general, "💬 ESCRÍBENOS AL PRIVADO", cierre_tit, 
        "Cotiza tu flasheo y catálogo de juegos", cierre_loc, "playstation 4 dualshock controller", archivos_temporales
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
