import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import re
import glob
import random
import asyncio
import subprocess
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
    """Genera locución natural y captura el timestamp exacto de cada palabra."""
    texto_limpio = limpiar_texto(texto)
    voces_rotadas = list(VOCES)
    random.shuffle(voces_rotadas)

    for voz in voces_rotadas:
        try:
            communicate = edge_tts.Communicate(texto_limpio, voz, rate="+4%")
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

def buscar_clips_locales():
    """Detecta clips propios en .github/clips/, clips/ o la raíz."""
    exts_validas = (".mp4", ".mov", ".mkv", ".webm")
    excluidos = {"noticia_tiktok.mp4"}
    encontrados = []

    for carpeta in [os.path.join(".github", "clips"), "clips"]:
        if os.path.isdir(carpeta):
            for archivo in sorted(os.listdir(carpeta)):
                ruta = os.path.join(carpeta, archivo)
                if os.path.isfile(ruta) and archivo.lower().endswith(exts_validas):
                    encontrados.append(ruta)

    for archivo in sorted(os.listdir(".")):
        if os.path.isfile(archivo) and archivo.lower() not in excluidos:
            if archivo.lower().startswith("clip") and archivo.lower().endswith(exts_validas):
                encontrados.append(archivo)

    return encontrados

def extraer_clip_con_ffmpeg(url_stream, ruta_salida, segundo_inicio=24, duracion=8):
    """Extrae un tramo de puro gameplay en vertical 720x1280 sin audio."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(segundo_inicio),
        "-t", str(duracion),
        "-i", url_stream,
        "-vf", "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-r", "30",
        "-an",
        ruta_salida
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=40)
        if os.path.exists(ruta_salida) and os.path.getsize(ruta_salida) > 100000:
            return True
    except Exception as e:
        print(f"FFmpeg timeout/error con stream: {e}")
    return False

def descargar_gameplay_real_steam(juegos_solicitados, max_clips=6):
    """Extrae hasta 6 clips de gameplay real entrando desde el segundo 22-45 para evitar intros y citas."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    cookies_edad = {"birthtime": "568022401", "lastagecheckage": "1-0-1988", "mature_content": "1"}
    clips_listos = []

    extras = [k for k in STEAM_APP_IDS.keys() if k not in [j.lower() for j in juegos_solicitados]]
    random.shuffle(extras)
    pool_juegos = list(juegos_solicitados) + extras[:4]

    for idx, juego in enumerate(pool_juegos):
        if len(clips_listos) >= max_clips:
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
            if res.status_code != 200:
                continue

            movies = res.json().get(str(app_id), {}).get("data", {}).get("movies", [])
            if not movies:
                continue

            # Preferir el segundo tráiler si existe (suele ser Gameplay Trailer puro)
            trailer = movies[1] if len(movies) > 1 else movies[0]
            stream_url = (
                trailer.get("mp4", {}).get("480")
                or trailer.get("webm", {}).get("480")
                or trailer.get("webm", {}).get("max")
                or trailer.get("hls_h264")
            )
            if not stream_url:
                continue

            ruta_mp4 = f"temp_gp_{idx}.mp4"
            # Entrar entre el segundo 22 y 42 donde los tráilers ya muestran combate/gameplay puro
            inicio_accion = random.randint(22, 42)
            print(f"Extrayendo gameplay en acción de {juego} (desde {inicio_accion}s)...")
            if extraer_clip_con_ffmpeg(stream_url, ruta_mp4, segundo_inicio=inicio_accion, duracion=8):
                print(f"[OK Gameplay MP4] {juego}")
                clips_listos.append(ruta_mp4)
        except Exception as e:
            print(f"Advertencia obteniendo stream de {juego}: {e}")

    return clips_listos

def descargar_fotos_ultimo_recurso(juegos_solicitados):
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
    """Prioriza 6+ gameplays en acción e intercala tus clips locales sin saturar."""
    clips_locales = buscar_clips_locales()
    clips_steam = descargar_gameplay_real_steam(juegos_solicitados, max_clips=6)

    if clips_steam:
        mezcla = []
        # Poner 1 clip de GoldHEN/consola al inicio, luego 3 gameplays, luego el otro clip local, y más gameplays
        if len(clips_locales) >= 1:
            mezcla.append(clips_locales[0])
        mezcla.extend(clips_steam[:3])
        if len(clips_locales) >= 2:
            mezcla.append(clips_locales[1])
        mezcla.extend(clips_steam[3:])
        print(f"Secuencia armada con {len(mezcla)} clips reales ({len(clips_steam)} gameplays + {len(clips_locales)} consola).")
        return mezcla

    if clips_locales:
        return clips_locales

    return descargar_fotos_ultimo_recurso(juegos_solicitados)

def ajustar_a_vertical_hd(clip, target_w=720, target_h=1280):
    w, h = clip.size
    if (w / h) > (target_w / target_h):
        clip = clip.resize(height=target_h)
    else:
        clip = clip.resize(width=target_w)
    return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)

def construir_fondo_dinamico(duracion_objetivo, lista_recursos):
    """Corta y mutea todos los clips con ritmo dinámico de 2.1s a 2.5s para cubrir 30+ segundos."""
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
        dur_corte = min(random.uniform(2.1, 2.5), duracion_objetivo - tiempo_acumulado)
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

                # Usar distintos tramos del clip si vuelve a salir
                ciclo = indice // len(pool)
                offset_ciclo = (ciclo * 2.5) % max(0.5, v.duration - dur_corte)
                max_start = max(0.0, v.duration - dur_corte - 0.1)
                start_t = min(max_start, offset_ciclo)

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

def crear_overlay_marca_persistente(duracion):
    """Barra superior e inferior de WALFEDW SERVICES visible durante todo el video."""
    w, h = 720, 1280
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        f_brand = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        f_sub = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except:
        f_brand = f_sub = ImageFont.load_default()

    draw.rounded_rectangle([60, 48, 660, 122], radius=24, fill=(8, 15, 30, 215), outline=(0, 210, 255, 255), width=3)
    draw.text((360, 74), "@WALFEDW • WALFEDW SERVICES", fill=(255, 255, 255, 255), anchor="mm", font=f_brand)
    draw.text((360, 102), "FLASHEO Y JUEGOS • PS3 • PS4 • PS5", fill=(0, 220, 255, 255), anchor="mm", font=f_sub)

    draw.rounded_rectangle([110, 1140, 610, 1192], radius=18, fill=(8, 15, 30, 205), outline=(255, 225, 0, 220), width=2)
    draw.text((360, 1166), "WHATSAPP: 914 899 697 • IG: @walfedw23", fill=(255, 230, 0, 255), anchor="mm", font=f_sub)

    ruta_png = "temp_brand_overlay.png"
    img.save(ruta_png)
    return ImageClip(ruta_png).set_duration(duracion), ruta_png

def renderizar_frame_subtitulo(palabras_grupo, indice_activo, idx_frame):
    """Dibuja subtítulos CapCut autoescalando la fuente si las palabras son muy largas (cero recortes)."""
    ancho, alto = 720, 220
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    palabras_upper = [p.upper() for p in palabras_grupo]
    tamano_fuente = 46
    espacio = 16

    while tamano_fuente >= 28:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", tamano_fuente)
        except:
            font = ImageFont.load_default()
            break
        anchos = [draw.textbbox((0, 0), p, font=font)[2] - draw.textbbox((0, 0), p, font=font)[0] for p in palabras_upper]
        ancho_total = sum(anchos) + espacio * (len(palabras_upper) - 1)
        if ancho_total <= 630:
            break
        tamano_fuente -= 3

    anchos = [draw.textbbox((0, 0), p, font=font)[2] - draw.textbbox((0, 0), p, font=font)[0] for p in palabras_upper]
    ancho_total = sum(anchos) + espacio * (len(palabras_upper) - 1)
    x_actual = (ancho - ancho_total) // 2
    y_texto = alto // 2

    for i, palabra in enumerate(palabras_upper):
        w_pal = anchos[i]
        if i == indice_activo:
            pad_x, pad_y = 12, 10
            draw.rounded_rectangle(
                [x_actual - pad_x, y_texto - 28 - pad_y, x_actual + w_pal + pad_x, y_texto + 28 + pad_y],
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
                .set_position(("center", 820))
            )
            clips_subs.append(clip_txt)

    return clips_subs, archivos_temp

def generar_flyer_profesional_hd(salida_png="temp_flyer_pro.png"):
    """Tarjeta HD de cierre para WALFEDW SERVICES (100% PlayStation, sin foto de Switch)."""
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

def obtener_clip_flyer_cierre(duracion_flyer=3.5):
    """Usa flyer_limpio.png si lo subes en el futuro, o la tarjeta profesional HD (ignora el flyer viejo con Switch)."""
    if os.path.exists("flyer_limpio.png"):
        clip_img = ImageClip("flyer_limpio.png").set_duration(duracion_flyer)
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
        "¿Sigues pagando precios absurdos por cada juego nuevo en tienda? Con lo que gastas en un solo disco, en Walfedw Services liberamos tu consola completa por software y sin riesgos."
    )
    juegos_visuales = datos_guion.get(
        "juegos_visuales",
        ["God of War Ragnarok", "Marvels Spider-Man 2", "Red Dead Redemption 2", "Ghost of Tsushima"]
    )

    print("1. Generando locución completa y tiempos de subtítulos...")
    audio_voz_path = "temp_voz_viral.mp3"
    tiempos_palabras = asyncio.run(generar_audio_con_tiempos(locucion, audio_voz_path))
    audio_voz = AudioFileClip(audio_voz_path).volumex(1.25)

    # Añadir 0.6s extra de respiro al final de la voz para que la última frase termine completa
    duracion_escena_principal = max(27.0, audio_voz.duration + 0.6)

    print("2. Extrayendo 6+ gameplays en acción...")
    lista_recursos = obtener_recursos_visuales(juegos_visuales)
    video_broll, clips_abiertos = construir_fondo_dinamico(duracion_escena_principal, lista_recursos)

    print("3. Añadiendo marca @WALFEDW y subtítulos autoajustados...")
    overlay_marca, ruta_marca_png = crear_overlay_marca_persistente(duracion_escena_principal)
    clips_subs, archivos_subs_temp = crear_subtitulos_capcut(tiempos_palabras, locucion, audio_voz.duration)

    escena_principal = CompositeVideoClip(
        [video_broll, overlay_marca] + clips_subs,
        size=(720, 1280)
    ).set_audio(audio_voz)

    print("4. Añadiendo cierre comercial HD (3.5s) para superar los 30 segundos...")
    clip_flyer = obtener_clip_flyer_cierre(duracion_flyer=3.5)
    video_completo = concatenate_videoclips([escena_principal, clip_flyer], method="compose")

    print("5. Mezclando música de fondo suave (9% volumen)...")
    bgm_path = descargar_musica_fondo()
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path)
            total_dur = video_completo.duration
            if bgm.duration < total_dur:
                n_loops = int(total_dur / bgm.duration) + 1
                bgm = concatenate_videoclips([bgm] * n_loops)
            bgm = bgm.subclip(0, total_dur).volumex(0.09)
            audio_final = CompositeAudioClip([video_completo.audio, bgm])
            video_completo = video_completo.set_audio(audio_final)
        except Exception as e:
            print(f"Advertencia BGM: {e}")

    print(f"6. Exportando MP4 final ({video_completo.duration:.1f} segundos)...")
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
        [audio_voz_path, "temp_bg_black.png", "temp_flyer_fallback.png", "temp_flyer_pro.png", ruta_marca_png]
        + archivos_subs_temp
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
