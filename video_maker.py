import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import re
import glob
import random
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

STEAM_APP_IDS = {
    "god of war ragnarok": "2322010",
    "god of war": "1593500",
    "marvels spider-man 2": "2651280",
    "marvels spider-man remastered": "1817070",
    "red dead redemption 2": "1174180",
    "grand theft auto v": "271590",
    "ghost of tsushima": "2215430",
    "the last of us part i": "1888930",
    "uncharted legacy of thieves": "1659420",
    "days gone": "1259420",
    "horizon forbidden west": "2420110",
    "cyberpunk 2077": "1091500",
    "elden ring": "1245620",
    "resident evil 4": "2050650",
    "silent hill 2": "2124490",
    "dragon ball sparking zero": "1790600",
    "mortal kombat 1": "1971870"
}

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?áéíóúÁÉÍÓÚñÑ\-]', '', texto).strip()

async def generar_audio_con_tiempos(texto, archivo_salida):
    """Genera locución clara y captura el tiempo exacto de cada palabra."""
    texto_limpio = limpiar_texto(texto)
    voces_rotadas = list(VOCES)
    random.shuffle(voces_rotadas)

    for voz in voces_rotadas:
        try:
            communicate = edge_tts.Communicate(texto_limpio, voz, rate="+8%")
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

def buscar_clips_sociales_automaticos(juegos_solicitados, max_videos=6):
    """Busca automáticamente clips de video .mp4 reales en redes (Astro Bot, GoldHEN, PS5, juegos top)."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WalfedwAutoBot/3.0"}

    # Consultas dinámicas: mezcla GoldHEN/PS4/PS5 con los juegos famosos del guion (ej. Astro Bot)
    endpoints = [
        "https://www.reddit.com/r/ps4homebrew/top.json?t=year&limit=25",
        "https://www.reddit.com/r/Astrobot/top.json?t=year&limit=25",
        "https://www.reddit.com/r/PS5/top.json?t=month&limit=25"
    ]
    for juego in juegos_solicitados[:3]:
        q = requests.utils.quote(f"{juego} gameplay")
        endpoints.append(f"https://www.reddit.com/search.json?q={q}&sort=top&t=year&limit=15")

    urls_mp4 = []
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            posts = res.json().get("data", {}).get("children", [])
            for p in posts:
                pdata = p.get("data", {})
                if pdata.get("over_18"):
                    continue
                media = pdata.get("secure_media") or pdata.get("media")
                if not media and pdata.get("crosspost_parent_list"):
                    media = pdata["crosspost_parent_list"][0].get("secure_media")

                if media and isinstance(media, dict) and "reddit_video" in media:
                    rv = media["reddit_video"]
                    dur = rv.get("duration", 0)
                    v_url = rv.get("fallback_url")
                    if v_url and 3 <= dur <= 90 and v_url not in urls_mp4:
                        urls_mp4.append(v_url)
        except Exception as e:
            print(f"Advertencia rastreando clips sociales: {e}")

    random.shuffle(urls_mp4)
    videos_descargados = []

    for idx, v_url in enumerate(urls_mp4):
        if len(videos_descargados) >= max_videos:
            break
        ruta_mp4 = f"temp_social_{idx}.mp4"
        try:
            with requests.get(v_url, headers=headers, stream=True, timeout=15) as r:
                if r.status_code == 200:
                    total = 0
                    with open(ruta_mp4, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                f.write(chunk)
                                total += len(chunk)
                                if total > 16 * 1024 * 1024:
                                    break
                    if os.path.exists(ruta_mp4) and os.path.getsize(ruta_mp4) > 120000:
                        print(f"[Clip Social MP4] Descargado ({len(videos_descargados)+1}/{max_videos})")
                        videos_descargados.append(ruta_mp4)
        except Exception:
            if os.path.exists(ruta_mp4):
                os.remove(ruta_mp4)

    return videos_descargados

def descargar_trailers_gameplay_steam(juegos_solicitados, max_trailers=3):
    """Descarga tráilers .mp4 de gameplay saltando el bloqueo de edad de Steam."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    cookies_edad = {"birthtime": "568022401", "lastagecheckage": "1-0-1988", "mature_content": "1"}
    trailers = []

    for idx, juego in enumerate(juegos_solicitados):
        if len(trailers) >= max_trailers:
            break
        clave = juego.lower().strip()
        app_id = STEAM_APP_IDS.get(clave)
        if not app_id:
            for k, v in STEAM_APP_IDS.items():
                if k in clave or clave in k:
                    app_id = v
                    break
        if not app_id:
            continue

        try:
            url_details = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US&l=english"
            res = requests.get(url_details, headers=headers, cookies=cookies_edad, timeout=10)
            if res.status_code == 200:
                movies = res.json().get(str(app_id), {}).get("data", {}).get("movies", [])
                if movies:
                    tr = random.choice(movies[:3])
                    mp4_urls = tr.get("mp4", {})
                    v_url = mp4_urls.get("480") or mp4_urls.get("max")
                    if v_url:
                        ruta = f"temp_gp_{idx}.mp4"
                        with requests.get(v_url, headers=headers, stream=True, timeout=18) as rv:
                            if rv.status_code == 200:
                                total = 0
                                with open(ruta, "wb") as f:
                                    for chunk in rv.iter_content(chunk_size=1024 * 256):
                                        if chunk:
                                            f.write(chunk)
                                            total += len(chunk)
                                            if total > 18 * 1024 * 1024:
                                                break
                                if os.path.exists(ruta) and os.path.getsize(ruta) > 150000:
                                    print(f"[Gameplay Trailer MP4] Descargado: {juego}")
                                    trailers.append(ruta)
        except Exception as e:
            print(f"Advertencia trailer {juego}: {e}")

    return trailers

def descargar_fotos_ultimo_recurso(juegos_solicitados):
    """SOLO se ejecuta si falla internet y no se pudieron bajar clips de video."""
    headers = {"User-Agent": "Mozilla/5.0"}
    fotos = []
    for idx, juego in enumerate(juegos_solicitados[:4]):
        clave = juego.lower().strip()
        app_id = STEAM_APP_IDS.get(clave, "2322010")
        url_p = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg"
        try:
            r = requests.get(url_p, headers=headers, timeout=10)
            if r.status_code == 200 and len(r.content) > 15000:
                ruta = f"temp_fallback_poster_{idx}.jpg"
                with open(ruta, "wb") as f:
                    f.write(r.content)
                fotos.append(ruta)
        except Exception:
            pass
    return fotos

def obtener_recursos_visuales(juegos_solicitados):
    """Prioridad 100% clips de VIDEO en movimiento; fotos solo como último recurso."""
    videos_sociales = buscar_clips_sociales_automaticos(juegos_solicitados, max_videos=5)
    videos_gameplay = descargar_trailers_gameplay_steam(juegos_solicitados, max_trailers=3)

    # Intercalar clips sociales (Astro Bot, GoldHEN, PS5) con gameplays
    mezcla_videos = []
    max_len = max(len(videos_sociales), len(videos_gameplay))
    for i in range(max_len):
        if i < len(videos_sociales):
            mezcla_videos.append(videos_sociales[i])
        if i < len(videos_gameplay):
            mezcla_videos.append(videos_gameplay[i])

    if len(mezcla_videos) >= 2:
        print(f"Modo 100% VIDEO activo: {len(mezcla_videos)} clips en movimiento listos.")
        return mezcla_videos

    print("Pocos videos obtenidos; activando respaldo de último recurso...")
    return mezcla_videos + descargar_fotos_ultimo_recurso(juegos_solicitados)

def ajustar_a_vertical_hd(clip, target_w=720, target_h=1280):
    w, h = clip.size
    if (w / h) > (target_w / target_h):
        clip = clip.resize(height=target_h)
    else:
        clip = clip.resize(width=target_w)
    return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)

def construir_fondo_dinamico(duracion_objetivo, lista_recursos):
    """Corta y mutea (.without_audio()) todos los clips con ritmo rápido de 1.7s a 2.1s."""
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
        dur_corte = min(random.uniform(1.7, 2.1), duracion_objetivo - tiempo_acumulado)
        if dur_corte <= 0.15:
            break

        try:
            if ruta.lower().endswith((".jpg", ".jpeg", ".png")):
                base = ImageClip(ruta).set_duration(dur_corte)
                base = ajustar_a_vertical_hd(base, 720, 1280)
                sub = base.resize(lambda t, d=dur_corte: 1.0 + 0.06 * (t / max(0.1, d))).set_position(("center", "center"))
                clips_abiertos.append(base)
            else:
                # MUTEO OBLIGATORIO del clip original para evitar ruido o copyright
                v = VideoFileClip(ruta).without_audio()
                clips_abiertos.append(v)

                min_start = 10.0 if ("temp_gp_" in ruta and v.duration > 15.0) else 0.0
                max_start = max(min_start, v.duration - dur_corte - 0.15)
                start_t = random.uniform(min_start, max_start) if max_start > min_start else min_start

                raw_sub = v.subclip(start_t, min(v.duration, start_t + dur_corte))
                raw_sub = ajustar_a_vertical_hd(raw_sub, 720, 1280)
                sub = raw_sub.resize(lambda t, d=dur_corte: 1.02 + 0.04 * (t / max(0.1, d))).set_position(("center", "center"))

            secuencia.append(sub)
            tiempo_acumulado += sub.duration
            errores = 0
        except Exception as e:
            print(f"Error editando {ruta}: {e}")
            errores += 1

    if not secuencia:
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), clips_abiertos

    video_concat = concatenate_videoclips(secuencia, method="compose")
    return video_concat.subclip(0, min(duracion_objetivo, video_concat.duration)), clips_abiertos

def renderizar_frame_subtitulo(palabras_grupo, indice_activo, idx_frame):
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
    """Genera tarjeta comercial HD limpia para WALFEDW SERVICES (100% PlayStation, cero Switch)."""
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
  body {
    width: 720px; height: 1280px;
    background: radial-gradient(circle at 50% 22%, #0d3266 0%, #050811 75%);
    color: #fff;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 58px 38px;
  }
  .top-badge {
    background: rgba(0, 210, 255, 0.15);
    border: 2px solid #00d2ff;
    color: #00d2ff;
    font-size: 22px; font-weight: 900; letter-spacing: 3px;
    padding: 12px 26px; border-radius: 50px;
    text-align: center; align-self: center;
    box-shadow: 0 0 25px rgba(0, 210, 255, 0.45);
  }
  .hero { text-align: center; }
  .ps-emblem {
    width: 140px; height: 140px; border-radius: 50%;
    margin: 0 auto 20px auto;
    background: linear-gradient(135deg, #0072ff, #00d2ff);
    display: flex; align-items: center; justify-content: center;
    font-size: 56px; font-weight: 900; color: #050811;
    box-shadow: 0 0 40px rgba(0, 210, 255, 0.8);
  }
  .title {
    font-size: 68px; font-weight: 900; letter-spacing: 2px;
    line-height: 1.05;
    text-shadow: 0 0 28px rgba(0, 210, 255, 0.85);
  }
  .subtitle {
    font-size: 34px; font-weight: 900; color: #ffe600;
    letter-spacing: 5px; margin-top: 8px;
  }
  .consoles-bar {
    background: linear-gradient(90deg, #0072ff, #00d2ff, #0072ff);
    color: #04070f;
    font-size: 38px; font-weight: 900; letter-spacing: 5px;
    padding: 18px; border-radius: 18px;
    text-align: center; margin: 26px 0 0 0;
    box-shadow: 0 0 32px rgba(0, 210, 255, 0.65);
  }
  .features {
    background: rgba(15, 23, 42, 0.9);
    border: 2px solid rgba(0, 210, 255, 0.55);
    border-radius: 24px;
    padding: 28px;
    display: flex; flex-direction: column; gap: 18px;
  }
  .feat-item {
    font-size: 26px; font-weight: 800; color: #f8fafc;
    display: flex; align-items: center; gap: 14px;
  }
  .dot {
    width: 16px; height: 16px; border-radius: 50%;
    background: #ffe600; box-shadow: 0 0 12px #ffe600;
    flex-shrink: 0;
  }
  .contact-box {
    background: #ffffff; color: #050811;
    border-radius: 24px; padding: 26px;
    text-align: center;
    box-shadow: 0 15px 35px rgba(0,0,0,0.85);
  }
  .wa-label { font-size: 21px; font-weight: 900; color: #16a34a; letter-spacing: 1px; }
  .wa-num { font-size: 48px; font-weight: 900; color: #050811; margin: 4px 0; }
  .ig-handle { font-size: 26px; font-weight: 800; color: #e11d48; }
</style>
</head>
<body>
  <div class="top-badge">CALIDAD • RAPIDEZ • CONFIANZA</div>
  <div class="hero">
    <div class="ps-emblem">W</div>
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
    # Si subes un flyer nuevo llamado flyer_oficial.png lo usará; si no, genera la tarjeta limpia sin Switch
    if os.path.exists("flyer_oficial.png"):
        clip_img = ImageClip("flyer_oficial.png").set_duration(duracion_flyer)
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
        "Trae tu PS3, PS4 o PS5 a Walfedw Services. Liberamos tu consola de forma segura y te la entregamos repleta con joyas como Astro Bot y God of War."
    )
    juegos_visuales = datos_guion.get(
        "juegos_visuales",
        ["Astro Bot", "God of War Ragnarok", "Marvels Spider-Man 2", "Red Dead Redemption 2"]
    )

    print("1. Generando voz limpia y capturando tiempos de subtítulos...")
    audio_voz_path = "temp_voz_viral.mp3"
    tiempos_palabras = asyncio.run(generar_audio_con_tiempos(locucion, audio_voz_path))
    # Potenciar ligeramente la voz para máxima claridad sobre la música
    audio_voz = AudioFileClip(audio_voz_path).volumex(1.25)
    duracion_voz = audio_voz.duration

    print("2. Rastreando clips de video en redes (Astro Bot, GoldHEN, PS5) y gameplays...")
    lista_recursos = obtener_recursos_visuales(juegos_visuales)
    video_broll, clips_abiertos = construir_fondo_dinamico(duracion_voz, lista_recursos)

    print("3. Renderizando subtítulos dinámicos estilo CapCut...")
    clips_subs, archivos_subs_temp = crear_subtitulos_capcut(tiempos_palabras, locucion, duracion_voz)

    escena_principal = CompositeVideoClip([video_broll] + clips_subs, size=(720, 1280)).set_audio(audio_voz)

    print("4. Añadiendo flyer comercial HD de cierre (2.8s)...")
    clip_flyer = obtener_clip_flyer_cierre(duracion_flyer=2.8)
    video_completo = concatenate_videoclips([escena_principal, clip_flyer], method="compose")

    print("5. Mezclando música de fondo suave (9% volumen para no tapar la voz)...")
    bgm_path = descargar_musica_fondo()
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path)
            total_dur = video_completo.duration
            if bgm.duration < total_dur:
                n_loops = int(total_dur / bgm.duration) + 1
                bgm = concatenate_videoclips([bgm] * n_loops)
            # Volumen bajo (0.09) para que la voz se escuche súper nítida
            bgm = bgm.subclip(0, total_dur).volumex(0.09)
            audio_final = CompositeAudioClip([video_completo.audio, bgm])
            video_completo = video_completo.set_audio(audio_final)
        except Exception as e:
            print(f"Advertencia BGM: {e}")

    print("6. Exportando MP4 final...")
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
        + glob.glob("temp_social_*.mp4")
        + glob.glob("temp_gp_*.mp4")
        + glob.glob("temp_fallback_poster_*.jpg")
    )

    for f in temporales:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
