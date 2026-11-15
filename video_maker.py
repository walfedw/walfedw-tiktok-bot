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

def buscar_app_id_dinamico(nombre_juego):
    """Consulta la API de búsqueda de Steam en vivo para encontrar cualquier juego del guion."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    limpio = re.sub(r'[^\w\s\-:]', '', nombre_juego).strip()
    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(limpio)}&l=english&cc=US"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                return str(items[0]["id"])
    except Exception as e:
        print(f"Error buscando AppID dinámico para {nombre_juego}: {e}")
    return None

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

def descargar_gameplay_dinamico(juegos_solicitados, max_clips=6):
    """Busca y descarga gameplays reales para los juegos PS4/PS3 elegidos por la IA."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    cookies_edad = {"birthtime": "568022401", "lastagecheckage": "1-0-1988", "mature_content": "1"}
    clips_listos = []

    for idx, juego in enumerate(juegos_solicitados):
        if len(clips_listos) >= max_clips:
            break
        app_id = buscar_app_id_dinamico(juego)
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

            trailers_elegidos = movies[:2] if len(juegos_solicitados) <= 3 else [movies[1] if len(movies) > 1 else movies[0]]
            for t_idx, trailer in enumerate(trailers_elegidos):
                if len(clips_listos) >= max_clips:
                    break
                stream_url = (
                    trailer.get("mp4", {}).get("480")
                    or trailer.get("webm", {}).get("480")
                    or trailer.get("webm", {}).get("max")
                    or trailer.get("hls_h264")
                )
                if not stream_url:
                    continue

                ruta_mp4 = f"temp_gp_{idx}_{t_idx}.mp4"
                inicio_accion = random.randint(20, 40)
                print(f"Extrayendo gameplay dinámico de '{juego}' (desde {inicio_accion}s)...")
                if extraer_clip_con_ffmpeg(stream_url, ruta_mp4, segundo_inicio=inicio_accion, duracion=8):
                    print(f"[OK Gameplay Dinámico] {juego}")
                    clips_listos.append(ruta_mp4)
        except Exception as e:
            print(f"Advertencia stream {juego}: {e}")

    return clips_listos

def descargar_clips_comunidad_por_juego(juegos_solicitados, max_clips=3):
    """Busca clips de gameplay en comunidades de PS4/PS3 para exclusivos de consola (ej. Bloodborne)."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WalfedwDynamicFinder/2.0)"}
    clips = []

    for idx, juego in enumerate(juegos_solicitados):
        if len(clips) >= max_clips:
            break
        q = requests.utils.quote(f"{juego} PS4 gameplay")
        url = f"https://www.reddit.com/search.json?q={q}&sort=top&t=year&limit=12"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            for post in res.json().get("data", {}).get("children", []):
                pdata = post.get("data", {})
                if pdata.get("over_18"):
                    continue
                media = pdata.get("secure_media") or pdata.get("media")
                if media and isinstance(media, dict) and "reddit_video" in media:
                    rv = media["reddit_video"]
                    v_url = rv.get("fallback_url")
                    if v_url and 4 <= rv.get("duration", 0) <= 90:
                        ruta_out = f"temp_comm_{idx}.mp4"
                        if extraer_clip_con_ffmpeg(v_url, ruta_out, segundo_inicio=2, duracion=7):
                            print(f"[OK Clip Comunidad PS4] {juego}")
                            clips.append(ruta_out)
                            break
        except Exception:
            continue

    return clips

def obtener_recursos_visuales(juegos_solicitados):
    """Combina gameplays dinámicos de PS4/PS3 con tus clips de GoldHEN/consola."""
    clips_locales = buscar_clips_locales()
    clips_steam = descargar_gameplay_dinamico(juegos_solicitados, max_clips=5)
    clips_comm = descargar_clips_comunidad_por_juego(juegos_solicitados, max_clips=3) if len(clips_steam) < 4 else []

    gameplays = clips_steam + clips_comm
    mezcla = []
    if len(clips_locales) >= 1:
        mezcla.append(clips_locales[0])
    mezcla.extend(gameplays[:3])
    if len(clips_locales) >= 2:
        mezcla.append(clips_locales[1])
    mezcla.extend(gameplays[3:])

    if mezcla:
        print(f"Recursos dinámicos listos: {len(gameplays)} gameplays + {len(clips_locales)} clips consola.")
        return mezcla

    fotos = []
    for idx, juego in enumerate(juegos_solicitados[:4]):
        app_id = buscar_app_id_dinamico(juego)
        if app_id:
            url_p = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/library_600x900_2x.jpg"
            try:
                r = requests.get(url_p, timeout=10)
                if r.status_code == 200 and len(r.content) > 15000:
                    ruta = f"temp_fallback_poster_{idx}.jpg"
                    with open(ruta, "wb") as f:
                        f.write(r.content)
                    fotos.append(ruta)
            except Exception:
                pass
    return fotos

def ajustar_a_vertical_hd(clip, target_w=720, target_h=1280):
    w, h = clip.size
    if (w / h) > (target_w / target_h):
        clip = clip.resize(height=target_h)
    else:
        clip = clip.resize(width=target_w)
    return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)

def construir_fondo_dinamico(duracion_objetivo, lista_recursos):
    """Corta y mutea todos los clips con ritmo dinámico de 2.1s a 2.5s."""
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
    """Barra superior e inferior dando prioridad a PS4 y PS3 (y soporte PS5)."""
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
    draw.text((360, 102), "FLASHEO PS4 Y PS3 • TAMBIÉN PS5", fill=(0, 220, 255, 255), anchor="mm", font=f_sub)

    draw.rounded_rectangle([90, 1140, 630, 1192], radius=18, fill=(8, 15, 30, 205), outline=(255, 225, 0, 220), width=2)
    draw.text((360, 1166), "CONSULTA TU VERSIÓN • WA: 914 899 697", fill=(255, 230, 0, 255), anchor="mm", font=f_sub)

    ruta_png = "temp_brand_overlay.png"
    img.save(ruta_png)
    return ImageClip(ruta_png).set_duration(duracion), ruta_png

def renderizar_frame_subtitulo(palabras_grupo, indice_activo, idx_frame):
    """Subtítulos estilo CapCut autoescalados para que nunca se corten a los lados."""
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

def obtener_clip_flyer_cierre(duracion_flyer=4.0):
    """Encuadra tu flyer.png de GitHub completo destacando PS4 y PS3 como especialidad."""
    canvas_w, canvas_h = 720, 1280
    lienzo = Image.new("RGB", (canvas_w, canvas_h), (8, 12, 26))
    draw = ImageDraw.Draw(lienzo)

    for y in range(canvas_h):
        r = int(12 + 18 * (1 - abs(y - 640) / 640))
        g = int(16 + 24 * (1 - abs(y - 640) / 640))
        b = int(38 + 45 * (1 - abs(y - 640) / 640))
        draw.line([(0, y), (canvas_w, y)], fill=(r, g, b))

    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
        f_sub = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        f_cta = ImageFont.truetype("DejaVuSans-Bold.ttf", 25)
        f_wa = ImageFont.truetype("DejaVuSans-Bold.ttf", 44)
        f_ig = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except:
        f_title = f_sub = f_cta = f_wa = f_ig = ImageFont.load_default()

    draw.text((360, 105), "WALFEDW SERVICES", fill=(255, 255, 255), anchor="mm", font=f_title)
    draw.rounded_rectangle([95, 148, 625, 198], radius=16, fill=(0, 210, 255))
    draw.text((360, 173), "FLASHEO E INSTALACIÓN DE JUEGOS", fill=(5, 10, 20), anchor="mm", font=f_cta)

    ruta_flyer = None
    for candidato in ["flyer.png", "flyer.jpg", "walfedw.jpg"]:
        if os.path.exists(candidato):
            ruta_flyer = candidato
            break

    y_fin_imagen = 650
    if ruta_flyer:
        print(f"Integrando tu imagen oficial completa de GitHub: {ruta_flyer}")
        foto = Image.open(ruta_flyer).convert("RGB")
        fw, fh = foto.size
        nuevo_w = 672
        nuevo_h = int(fh * (nuevo_w / fw))
        if nuevo_h > 540:
            nuevo_h = 540
            nuevo_w = int(fw * (nuevo_h / fh))

        resample_mode = getattr(Image, "Resampling", Image).LANCZOS
        foto_resized = foto.resize((nuevo_w, nuevo_h), resample_mode)

        x_pos = (canvas_w - nuevo_w) // 2
        y_pos = 235

        draw.rounded_rectangle(
            [x_pos - 6, y_pos - 6, x_pos + nuevo_w + 6, y_pos + nuevo_h + 6],
            radius=22,
            outline=(0, 210, 255),
            width=6
        )
        lienzo.paste(foto_resized, (x_pos, y_pos))
        y_fin_imagen = y_pos + nuevo_h + 32

    draw.rounded_rectangle([45, y_fin_imagen, 675, y_fin_imagen + 135], radius=22, fill=(15, 25, 48), outline=(255, 230, 0), width=3)
    draw.text((360, y_fin_imagen + 36), "• CONSULTA LA VERSIÓN DE TU CONSOLA", fill=(255, 230, 0), anchor="mm", font=f_cta)
    draw.text((360, y_fin_imagen + 76), "• DIME QUÉ JUEGOS TE GUSTAN", fill=(255, 255, 255), anchor="mm", font=f_cta)
    draw.text((360, y_fin_imagen + 112), "ESPECIALISTAS EN PS4 Y PS3 • TAMBIÉN PS5", fill=(0, 220, 255), anchor="mm", font=f_sub)

    y_contacto = y_fin_imagen + 160
    draw.rounded_rectangle([45, y_contacto, 675, y_contacto + 175], radius=24, fill=(255, 255, 255))
    draw.text((360, y_contacto + 32), "ESCRÍBENOS AL WHATSAPP", fill=(22, 163, 74), anchor="mm", font=f_cta)
    draw.text((360, y_contacto + 82), "914 899 697", fill=(5, 8, 17), anchor="mm", font=f_wa)
    draw.text((360, y_contacto + 136), "INSTAGRAM: @walfedw23", fill=(225, 29, 72), anchor="mm", font=f_ig)

    salida_tmp = "temp_flyer_github_card.png"
    lienzo.save(salida_tmp)

    clip_img = ImageClip(salida_tmp).set_duration(duracion_flyer)
    return clip_img.resize(lambda t: 1.03 - 0.03 * (t / duracion_flyer)).set_position(("center", "center"))

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
        "¿Tienes una PS4 o PS3 en casa y sigues pagando carísimo por cada juego? En Walfedw Services yo me encargo de flashear tu consola e instalarte los mejores títulos. Consulta tu versión y dime qué juegos te gustan."
    )
    juegos_visuales = datos_guion.get(
        "juegos_visuales",
        ["God of War Ragnarok", "Ghost of Tsushima", "Red Dead Redemption 2", "Grand Theft Auto V"]
    )

    print("1. Generando locución completa y tiempos de subtítulos...")
    audio_voz_path = "temp_voz_viral.mp3"
    tiempos_palabras = asyncio.run(generar_audio_con_tiempos(locucion, audio_voz_path))
    audio_voz = AudioFileClip(audio_voz_path).volumex(1.25)

    duracion_escena_principal = max(27.0, audio_voz.duration + 0.6)

    print("2. Buscando y extrayendo gameplays de PS4/PS3 para:", juegos_visuales)
    lista_recursos = obtener_recursos_visuales(juegos_visuales)
    video_broll, clips_abiertos = construir_fondo_dinamico(duracion_escena_principal, lista_recursos)

    print("3. Añadiendo marca @WALFEDW (PS4 y PS3) y subtítulos autoajustados...")
    overlay_marca, ruta_marca_png = crear_overlay_marca_persistente(duracion_escena_principal)
    clips_subs, archivos_subs_temp = crear_subtitulos_capcut(tiempos_palabras, locucion, audio_voz.duration)

    escena_principal = CompositeVideoClip(
        [video_broll, overlay_marca] + clips_subs,
        size=(720, 1280)
    ).set_audio(audio_voz)

    print("4. Cerrando con tu flyer.png oficial de GitHub (4.0s)...")
    clip_flyer = obtener_clip_flyer_cierre(duracion_flyer=4.0)
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
        [audio_voz_path, "temp_bg_black.png", "temp_flyer_github_card.png", ruta_marca_png]
        + archivos_subs_temp
        + glob.glob("temp_gp_*.mp4")
        + glob.glob("temp_comm_*.mp4")
        + glob.glob("temp_fallback_poster_*.jpg")
    )

    for f in temporales:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    return archivo_salida
