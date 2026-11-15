import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import re
import glob
import random
import base64
import asyncio
import requests
import edge_tts
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips
)

VOCES = ["es-MX-JorgeNeural", "es-MX-DarianNeural", "es-ES-AlvaroNeural"]
URL_BGM_GAMING = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73229.mp3"

# Mapa de AppIDs para descargar clips de GAMEPLAY REAL (.mp4) y pósteres HD
STEAM_APP_IDS = {
    "god of war ragnarok": "2322010",
    "god of war": "1593500",
    "marvels spider-man remastered": "1817070",
    "marvels spider-man miles morales": "1817190",
    "red dead redemption 2": "1174180",
    "grand theft auto v": "271590",
    "ghost of tsushima": "2215430",
    "the last of us part i": "1888930",
    "uncharted legacy of thieves": "1659420",
    "days gone": "1259420",
    "horizon zero dawn": "1151640",
    "horizon forbidden west": "2420110",
    "cyberpunk 2077": "1091500",
    "elden ring": "1245620",
    "resident evil 4": "2050650",
    "silent hill 2": "2124490",
    "dragon ball sparking zero": "1790600",
    "mortal kombat 1": "1971870",
    "detroit become human": "1222140"
}

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?áéíóúÁÉÍÓÚñÑ\-]', '', texto).strip()

async def generar_audio_con_tiempos(texto, archivo_salida):
    """Genera locución con rotación de voz y captura el tiempo exacto de cada palabra."""
    texto_limpio = limpiar_texto(texto)
    voces_rotadas = list(VOCES)
    random.shuffle(voces_rotadas)

    for voz in voces_rotadas:
        try:
            communicate = edge_tts.Communicate(texto_limpio, voz, rate="+6%")
            tiempos_palabras = []
            with open(archivo_salida, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        inicio = chunk["offset"] / 10_000_000.0
                        dur = chunk["duration"] / 10_000_000.0
                        tiempos_palabras.append({
                            "palabra": chunk["text"],
                            "inicio": inicio,
                            "fin": inicio + dur
                        })
            if os.path.exists(archivo_salida) and os.path.getsize(archivo_salida) > 1000:
                print(f"Voz utilizada: {voz}")
                return tiempos_palabras
        except Exception as e:
            print(f"Advertencia con voz {voz}: {e}")
    raise RuntimeError("No se pudo generar el audio de locución.")

def buscar_app_id(nombre_juego):
    clave = nombre_juego.lower().strip()
    if clave in STEAM_APP_IDS:
        return STEAM_APP_IDS[clave]
    for k, v in STEAM_APP_IDS.items():
        if k in clave or clave in k:
            return v
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url_api = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(nombre_juego)}&l=english&cc=US"
        r = requests.get(url_api, headers=headers, timeout=8)
        if r.status_code == 200 and r.json().get("items"):
            return str(r.json()["items"][0]["id"])
    except Exception:
        pass
    return None

def descargar_gameplay_mp4(nombre_juego, idx):
    """Descarga un video .mp4 real de gameplay oficial del juego."""
    app_id = buscar_app_id(nombre_juego)
    if not app_id:
        return None

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        url_details = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US&l=english"
        res = requests.get(url_details, headers=headers, timeout=10)
        if res.status_code != 200:
            return None

        data = res.json().get(str(app_id), {}).get("data", {})
        movies = data.get("movies", [])
        if not movies:
            return None

        # Elegir un tráiler aleatorio si el juego tiene varios
        trailer = random.choice(movies[:3])
        mp4_urls = trailer.get("mp4", {})
        video_url = mp4_urls.get("480") or mp4_urls.get("max")
        if not video_url:
            return None

        ruta_mp4 = f"temp_gameplay_{idx}.mp4"
        with requests.get(video_url, headers=headers, stream=True, timeout=20) as r_vid:
            if r_vid.status_code == 200:
                bytes_descargados = 0
                limite_bytes = 22 * 1024 * 1024  # Tope 22 MB para descarga veloz
                with open(ruta_mp4, "wb") as f:
                    for chunk in r_vid.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                            bytes_descargados += len(chunk)
                            if bytes_descargados >= limite_bytes:
                                break
                if os.path.exists(ruta_mp4) and os.path.getsize(ruta_mp4) > 150000:
                    print(f"[Gameplay Real MP4] Descargado: {nombre_juego}")
                    return ruta_mp4
    except Exception as e:
        print(f"Advertencia descargando gameplay de {nombre_juego}: {e}")

    # Si ese juego no tuviera tráiler MP4, descargar su póster vertical HD 600x900
    try:
        url_poster = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg"
        r_img = requests.get(url_poster, headers=headers, timeout=10)
        if r_img.status_code == 200 and len(r_img.content) > 15000:
            ruta_jpg = f"temp_poster_{idx}.jpg"
            with open(ruta_jpg, "wb") as f:
                f.write(r_img.content)
            return ruta_jpg
    except Exception:
        pass

    return None

def obtener_recursos_visuales(juegos_solicitados):
    """Intercala tus clips reales de GoldHEN/consola (clips/) con gameplays MP4 descargados."""
    extensiones = ("clips/*.mp4", "clips/*.MP4", "clips/*.mov", "clips/*.MOV", "clips/*.jpg", "clips/*.png")
    clips_taller = []
    for ext in extensiones:
        clips_taller.extend(glob.glob(ext))
    random.shuffle(clips_taller)

    gameplays_descargados = []
    for idx, juego in enumerate(juegos_solicitados):
        recurso = descargar_gameplay_mp4(juego, idx)
        if recurso:
            gameplays_descargados.append(recurso)

    # Intercalar: [Clip GoldHEN/Consola, Gameplay 1, Clip GoldHEN/Consola, Gameplay 2...]
    mezcla = []
    max_len = max(len(clips_taller), len(gameplays_descargados))
    for i in range(max_len):
        if i < len(clips_taller):
            mezcla.append(clips_taller[i])
        if i < len(gameplays_descargados):
            mezcla.append(gameplays_descargados[i])

    print(f"Recursos listos: {len(clips_taller)} clips locales + {len(gameplays_descargados)} gameplays HD.")
    return mezcla

def ajustar_a_vertical_hd(clip, target_w=720, target_h=1280):
    """Escala y recorta a 720x1280 en pantalla completa sin bordes negros."""
    w, h = clip.size
    if (w / h) > (target_w / target_h):
        clip = clip.resize(height=target_h)
    else:
        clip = clip.resize(width=target_w)
    return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)

def construir_fondo_dinamico(duracion_objetivo, lista_recursos):
    """Arma cortes rápidos dinámicos cada ~2.0 segundos entrando directo en la acción."""
    secuencia = []
    tiempo_acumulado = 0.0
    clips_abiertos = []

    pool = [r for r in lista_recursos if os.path.exists(r)]
    if not pool:
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), clips_abiertos

    indice = 0
    errores = 0

    while tiempo_acumulado < duracion_objetivo and errores < len(pool) * 2:
        ruta = pool[indice % len(pool)]
        indice += 1
        dur_corte = min(random.uniform(1.8, 2.3), duracion_objetivo - tiempo_acumulado)
        if dur_corte <= 0.15:
            break

        try:
            if ruta.lower().endswith((".jpg", ".jpeg", ".png")):
                base = ImageClip(ruta).set_duration(dur_corte)
                base = ajustar_a_vertical_hd(base, 720, 1280)
                sub = base.resize(lambda t, d=dur_corte: 1.0 + 0.05 * (t / max(0.1, d))).set_position(("center", "center"))
                clips_abiertos.append(base)
            else:
                v = VideoFileClip(ruta).without_audio()
                clips_abiertos.append(v)

                # Si es un tráiler largo (>16s), saltar los primeros 11s para evitar logos de clasificación
                min_start = 11.0 if v.duration > 16.0 else 0.0
                max_start = max(min_start, v.duration - dur_corte - 0.2)
                start_t = random.uniform(min_start, max_start) if max_start > min_start else min_start

                sub = v.subclip(start_t, min(v.duration, start_t + dur_corte))
                sub = ajustar_a_vertical_hd(sub, 720, 1280)

            secuencia.append(sub)
            tiempo_acumulado += sub.duration
            errores = 0
        except Exception as e:
            print(f"Error procesando {ruta}: {e}")
            errores += 1

    if not secuencia:
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), clips_abiertos

    video_concat = concatenate_videoclips(secuencia, method="compose")
    return video_concat.subclip(0, min(duracion_objetivo, video_concat.duration)), clips_abiertos

def renderizar_frame_subtitulo(palabras_grupo, indice_activo, idx_frame):
    """Subtítulos virales estilo CapCut con caja rosa neón sobre palabra activa."""
    ancho, alto = 720, 220
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
    except:
        font = ImageFont.load_default()

    palabras_upper = [p.upper() for p in palabras_grupo]
    espacio = 16
    anchos = []
    for p in palabras_upper:
        bbox = draw.textbbox((0, 0), p, font=font)
        anchos.append(bbox[2] - bbox[0])

    ancho_total = sum(anchos) + espacio * (len(palabras_upper) - 1)
    x_actual = (ancho - ancho_total) // 2
    y_texto = alto // 2

    for i, palabra in enumerate(palabras_upper):
        w_pal = anchos[i]
        if i == indice_activo:
            pad_x, pad_y = 12, 10
            draw.rounded_rectangle(
                [x_actual - pad_x, y_texto - 30 - pad_y, x_actual + w_pal + pad_x, y_texto + 30 + pad_y],
                radius=14,
                fill=(235, 30, 110, 255)
            )

        for dx, dy in [(-4,-4), (4,-4), (-4,4), (4,4), (-4,0), (4,0), (0,-4), (0,4)]:
            draw.text((x_actual + dx, y_texto + dy), palabra, fill=(0, 0, 0, 255), anchor="lm", font=font)

        draw.text((x_actual, y_texto), palabra, fill=(255, 255, 255, 255), anchor="lm", font=font)
        x_actual += w_pal + espacio

    nombre_png = f"temp_capcut_{idx_frame}.png"
    img.save(nombre_png)
    return nombre_png

def crear_subtitulos_capcut(tiempos_palabras, texto_completo, duracion_total):
    if not tiempos_palabras:
        palabras = limpiar_texto(texto_completo).split()
        if not palabras:
            return [], []
        paso = duracion_total / len(palabras)
        tiempos_palabras = [
            {"palabra": p, "inicio": i * paso, "fin": (i + 1) * paso}
            for i, p in enumerate(palabras)
        ]

    clips_subs = []
    archivos_temp = []
    frame_id = 0

    for i in range(0, len(tiempos_palabras), 3):
        grupo = tiempos_palabras[i:i+3]
        textos_grupo = [g["palabra"] for g in grupo]

        for j, item in enumerate(grupo):
            t_ini = item["inicio"]
            t_fin = grupo[j + 1]["inicio"] if (j + 1) < len(grupo) else (
                tiempos_palabras[i + 3]["inicio"] if (i + 3) < len(tiempos_palabras) else duracion_total
            )
            dur = max(0.08, t_fin - t_ini)

            png_path = renderizar_frame_subtitulo(textos_grupo, j, frame_id)
            frame_id += 1
            archivos_temp.append(png_path)

            clip_txt = (
                ImageClip(png_path)
                .set_start(t_ini)
                .set_duration(dur)
                .set_position(("center", 800))
            )
            clips_subs.append(clip_txt)

    return clips_subs, archivos_temp

def generar_flyer_profesional_hd(salida_png="temp_flyer_pro.png"):
    """Renderiza tarjeta HD final de WALFEDW SERVICES (PS3 • PS4 • PS5)."""
    avatar_tag = ""
    if os.path.exists("walfedw.jpg"):
        try:
            with open("walfedw.jpg", "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                avatar_tag = f"<img src='data:image/jpeg;base64,{b64}' class='avatar' />"
        except Exception:
            pass

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }}
  body {{
    width: 720px; height: 1280px;
    background: radial-gradient(circle at 50% 25%, #0f294a 0%, #050811 75%);
    color: #fff;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 55px 38px;
  }}
  .top-badge {{
    background: rgba(0, 210, 255, 0.15);
    border: 2px solid #00d2ff;
    color: #00d2ff;
    font-size: 22px; font-weight: 900; letter-spacing: 3px;
    padding: 12px 24px; border-radius: 50px;
    text-align: center; align-self: center;
    box-shadow: 0 0 25px rgba(0, 210, 255, 0.4);
  }}
  .hero {{ text-align: center; margin-top: 10px; }}
  .avatar {{
    width: 170px; height: 170px; border-radius: 50%;
    border: 4px solid #00d2ff;
    box-shadow: 0 0 35px rgba(0, 210, 255, 0.85);
    object-fit: cover; object-position: top center;
    margin-bottom: 18px;
  }}
  .title {{
    font-size: 62px; font-weight: 900; letter-spacing: 2px;
    line-height: 1.05;
    text-shadow: 0 0 25px rgba(0, 210, 255, 0.8);
  }}
  .subtitle {{
    font-size: 32px; font-weight: 900; color: #ffe600;
    letter-spacing: 4px; margin-top: 8px;
  }}
  .consoles-bar {{
    background: linear-gradient(90deg, #0072ff, #00d2ff, #0072ff);
    color: #04070f;
    font-size: 36px; font-weight: 900; letter-spacing: 4px;
    padding: 16px; border-radius: 18px;
    text-align: center; margin: 24px 0;
    box-shadow: 0 0 30px rgba(0, 210, 255, 0.6);
  }}
  .features {{
    background: rgba(15, 23, 42, 0.88);
    border: 2px solid rgba(0, 210, 255, 0.5);
    border-radius: 24px;
    padding: 26px 28px;
    display: flex; flex-direction: column; gap: 16px;
  }}
  .feat-item {{
    font-size: 26px; font-weight: 800; color: #f8fafc;
    display: flex; align-items: center; gap: 14px;
  }}
  .dot {{
    width: 16px; height: 16px; border-radius: 50%;
    background: #ffe600; box-shadow: 0 0 10px #ffe600;
    flex-shrink: 0;
  }}
  .contact-box {{
    background: #ffffff; color: #050811;
    border-radius: 24px; padding: 24px;
    text-align: center;
    box-shadow: 0 15px 35px rgba(0,0,0,0.8);
  }}
  .wa-label {{ font-size: 20px; font-weight: 900; color: #16a34a; letter-spacing: 1px; }}
  .wa-num {{ font-size: 46px; font-weight: 900; color: #050811; margin: 4px 0; }}
  .ig-handle {{ font-size: 26px; font-weight: 800; color: #e11d48; }}
</style>
</head>
<body>
  <div class="top-badge">CALIDAD • RAPIDEZ • CONFIANZA</div>
  <div class="hero">
    {avatar_tag}
    <div class="title">WALFEDW</div>
    <div class="subtitle">SERVICES</div>
    <div class="consoles-bar">PS3 • PS4 • PS5</div>
  </div>
  <div class="features">
    <div class="feat-item"><span class="dot"></span>FLASHEO 100% SEGURO POR SOFTWARE</div>
    <div class="feat-item"><span class="dot"></span>INSTALACIÓN DE JUEGOS Y DLC</div>
    <div class="feat-item"><span class="dot"></span>PARCHES 60 FPS Y MODS EXCLUSIVOS</div>
    <div class="feat-item"><span class="dot"></span>GARANTÍA Y RESPALDO TÉCNICO</div>
  </div>
  <div class="contact-box">
    <div class="wa-label">ESCRÍBENOS AL WHATSAPP</div>
    <div class="wa-num">914 899 697</div>
    <div class="ig-handle">INSTAGRAM: @walfedw23</div>
  </div>
</body>
</html>"""

    html_tmp = "temp_flyer_card.html"
    with open(html_tmp, "w", encoding="utf-8") as f:
        f.write(html)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 720, "height": 1280})
            page.goto(f"file://{os.path.abspath(html_tmp)}")
            page.screenshot(path=salida_png)
            browser.close()
        if os.path.exists(html_tmp):
            os.remove(html_tmp)
        return salida_png
    except Exception as e:
        print(f"Advertencia renderizando flyer HTML: {e}")
        return None

def obtener_clip_flyer_cierre(duracion_flyer=2.8):
    for candidato in ["flyer.jpg", "flyer.png", "walfedw_flyer.jpg"]:
        if os.path.exists(candidato):
            clip_img = ImageClip(candidato).set_duration(duracion_flyer)
            clip_img = ajustar_a_vertical_hd(clip_img, 720, 1280)
            return clip_img.resize(lambda t: 1.04 - 0.04 * (t / duracion_flyer)).set_position(("center", "center"))

    png_generado = generar_flyer_profesional_hd("temp_flyer_pro.png")
    if png_generado and os.path.exists(png_generado):
        clip_img = ImageClip(png_generado).set_duration(duracion_flyer)
        return clip_img.resize(lambda t: 1.03 - 0.03 * (t / duracion_flyer)).set_position(("center", "center"))

    img = Image.new("RGB", (720, 1280), (8, 14, 28))
    img.save("temp_flyer_fallback.png")
    return ImageClip("temp_flyer_fallback.png").set_duration(duracion_flyer)

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

def crear_video(datos_guion, archivo_salida="noticia_tiktok.mp4"):
    locucion = datos_guion.get(
        "locucion_completa",
        "Trae tu PS3, PS4 o PS5 a Walfedw Services. Liberamos tu consola de forma segura y te la entregamos repleta con los mejores juegos."
    )
    juegos_visuales = datos_guion.get(
        "juegos_visuales",
        ["God of War Ragnarok", "Marvels Spider-Man Remastered", "Red Dead Redemption 2", "Ghost of Tsushima"]
    )

    print("1. Generando locución con sincronización palabra por palabra...")
    audio_voz_path = "temp_voz_viral.mp3"
    tiempos_palabras = asyncio.run(generar_audio_con_tiempos(locucion, audio_voz_path))
    audio_voz = AudioFileClip(audio_voz_path)
    duracion_voz = audio_voz.duration

    print("2. Descargando clips de gameplay real (.mp4) y preparando cortes rápidos...")
    lista_recursos = obtener_recursos_visuales(juegos_visuales)
    video_broll, clips_abiertos = construir_fondo_dinamico(duracion_voz, lista_recursos)

    print("3. Renderizando subtítulos dinámicos estilo CapCut...")
    clips_subs, archivos_subs_temp = crear_subtitulos_capcut(tiempos_palabras, locucion, duracion_voz)

    escena_principal = CompositeVideoClip([video_broll] + clips_subs, size=(720, 1280)).set_audio(audio_voz)

    print("4. Añadiendo flyer comercial HD de cierre (2.8s)...")
    clip_flyer = obtener_clip_flyer_cierre(duracion_flyer=2.8)
    video_completo = concatenate_videoclips([escena_principal, clip_flyer], method="compose")

    print("5. Mezclando beat gaming de fondo...")
    bgm_path = descargar_musica_fondo()
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path)
            total_dur = video_completo.duration
            if bgm.duration < total_dur:
                n_loops = int(total_dur / bgm.duration) + 1
                bgm = concatenate_videoclips([bgm] * n_loops)
            bgm = bgm.subclip(0, total_dur).volumex(0.16)
            audio_final = CompositeAudioClip([video_completo.audio, bgm])
            video_completo = video_completo.set_audio(audio_final)
        except Exception as e:
            print(f"Advertencia BGM: {e}")

    print("6. Exportando MP4 en alta calidad...")
    video_completo.write_videofile(
        archivo_salida,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True
    )

    video_completo.close()
    audio_voz.close()
    for c in clips_abiertos:
        try:
            c.close()
        except:
            pass

    temporales = (
        [audio_voz_path, "temp_bg_black.png", "temp_flyer_fallback.png", "temp_flyer_pro.png"]
        + archivos_subs_temp
        + glob.glob("temp_poster_*.jpg")
        + glob.glob("temp_gameplay_*.mp4")
    )

    for f in temporales:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
