import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = getattr(PIL.Image, 'LANCZOS', getattr(PIL.Image, 'BICUBIC', None))

import os
import re
import json
import glob
import math
import random
import asyncio
import subprocess
import requests
import numpy as np
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.editor import (
    VideoFileClip,
    VideoClip,
    ImageClip,
    ColorClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    concatenate_audioclips
)

HISTORIAL_FILE = "historial.json"
VOCES = ["es-MX-JorgeNeural", "es-MX-DarianNeural", "es-ES-AlvaroNeural"]
URL_BGM_GAMING = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73229.mp3"

def cargar_yt_usados():
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return set(data.get("youtube_ids", []))
        except Exception:
            pass
    return set()

def registrar_yt_usado(video_id):
    if not video_id:
        return
    data = {"temas": [], "ganchos": [], "juegos": [], "youtube_ids": []}
    if os.path.exists(HISTORIAL_FILE):
        try:
            with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data.update(loaded)
        except Exception:
            pass
    yt_list = data.setdefault("youtube_ids", [])
    if video_id not in yt_list:
        yt_list.append(video_id)
    data["youtube_ids"] = yt_list[-80:]
    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def asegurar_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        try:
            subprocess.run(["pip", "install", "-q", "-U", "yt-dlp"], check=True)
            return True
        except Exception:
            return False

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?áéíóúÁÉÍÓÚñÑ\-]', '', texto).strip()

async def generar_audio_con_tiempos(texto, archivo_salida):
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

def buscar_clips_locales():
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

def extraer_clip_con_ffmpeg(url_stream, ruta_salida, segundo_inicio=25, duracion=8):
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
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
        if os.path.exists(ruta_salida) and os.path.getsize(ruta_salida) > 100000:
            return True
    except Exception:
        pass
    return False

def descargar_clips_youtube(busquedas_youtube, juegos_solicitados, max_clips=4):
    """Extrae clips de YouTube usando clientes embebidos que evitan bloqueo en GitHub Actions."""
    if not asegurar_yt_dlp():
        return []

    yt_usados = cargar_yt_usados()
    consultas = list(busquedas_youtube or [])
    for j in juegos_solicitados:
        q_extra = f"{j} PS4 gameplay no commentary"
        if q_extra not in consultas:
            consultas.append(q_extra)

    clips_yt = []
    for idx, query in enumerate(consultas):
        if len(clips_yt) >= max_clips:
            break
        try:
            res = subprocess.run(
                [
                    "yt-dlp",
                    "--no-warnings",
                    "--extractor-args", "youtube:player_client=tv_embedded,ios",
                    "--dump-single-json",
                    "--flat-playlist",
                    f"ytsearch6:{query}"
                ],
                capture_output=True, text=True, timeout=22
            )
            if res.returncode != 0 or not res.stdout.strip():
                continue

            entries = json.loads(res.stdout).get("entries", [])
            nuevos = [e for e in entries if e.get("id") and f"yt:{e.get('id')}" not in yt_usados]
            candidatos = nuevos if nuevos else entries
            random.shuffle(candidatos)

            for entry in candidatos:
                vid_id = entry.get("id")
                dur = entry.get("duration") or 0
                if not vid_id or (dur and (dur < 35 or dur > 2400)):
                    continue

                vid_url = f"https://www.youtube.com/watch?v={vid_id}"
                g_res = subprocess.run(
                    [
                        "yt-dlp",
                        "--no-warnings",
                        "--extractor-args", "youtube:player_client=tv_embedded,ios",
                        "-f", "best[height<=720][ext=mp4]/best[height<=720]/best",
                        "-g", vid_url
                    ],
                    capture_output=True, text=True, timeout=22
                )
                stream_url = g_res.stdout.strip().splitlines()[0] if g_res.stdout.strip() else ""
                if not stream_url:
                    continue

                ruta_mp4 = f"temp_yt_{idx}.mp4"
                inicio = random.randint(20, 45)
                if extraer_clip_con_ffmpeg(stream_url, ruta_mp4, segundo_inicio=inicio, duracion=8):
                    tag_id = f"yt:{vid_id}"
                    print(f"[OK YouTube Nuevo ({tag_id})] {query}")
                    registrar_yt_usado(tag_id)
                    yt_usados.add(tag_id)
                    clips_yt.append(ruta_mp4)
                    break
        except Exception as e:
            print(f"Advertencia YouTube ({query}): {e}")

    return clips_yt

def descargar_clips_comunidad_ps4(juegos_solicitados, max_clips=3):
    """Extrae clips reales de menús GoldHEN/HEN y gameplays desde comunidades PS4/PS3 sin bloqueo."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WalfedwEditorBot/3.0)"}
    yt_usados = cargar_yt_usados()
    busquedas = ["GoldHEN PS4 60fps", "PS4 homebrew menu"] + [f"{j} PS4" for j in juegos_solicitados[:2]]
    clips = []

    for idx, q_raw in enumerate(busquedas):
        if len(clips) >= max_clips:
            break
        q = requests.utils.quote(q_raw)
        url = f"https://www.reddit.com/search.json?q={q}&sort=top&t=year&limit=15"
        try:
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code != 200:
                continue
            posts = res.json().get("data", {}).get("children", [])
            random.shuffle(posts)
            for post in posts:
                pdata = post.get("data", {})
                pid = pdata.get("id")
                tag_id = f"rd:{pid}"
                if not pid or tag_id in yt_usados or pdata.get("over_18"):
                    continue
                media = pdata.get("secure_media") or pdata.get("media")
                if media and isinstance(media, dict) and "reddit_video" in media:
                    rv = media["reddit_video"]
                    v_url = rv.get("fallback_url")
                    if v_url and 5 <= rv.get("duration", 0) <= 120:
                        ruta_out = f"temp_comm_{idx}.mp4"
                        if extraer_clip_con_ffmpeg(v_url, ruta_out, segundo_inicio=2, duracion=7):
                            print(f"[OK Comunidad PS4/PS3 ({tag_id})] {q_raw}")
                            registrar_yt_usado(tag_id)
                            yt_usados.add(tag_id)
                            clips.append(ruta_out)
                            break
        except Exception:
            continue

    return clips

def buscar_app_id_dinamico(nombre_juego):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    limpio = re.sub(r'[^\w\s\-:]', '', nombre_juego).strip()
    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(limpio)}&l=english&cc=US"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                return str(items[0]["id"])
    except Exception:
        pass
    return None

def descargar_gameplay_steam_respaldo(juegos_solicitados, max_clips=4):
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
            inicio_accion = random.randint(20, 40)
            if extraer_clip_con_ffmpeg(stream_url, ruta_mp4, segundo_inicio=inicio_accion, duracion=8):
                print(f"[OK Steam Gameplay] {juego}")
                clips_listos.append(ruta_mp4)
        except Exception:
            pass

    return clips_listos

def obtener_recursos_visuales(busquedas_youtube, juegos_solicitados):
    """Combina YouTube + Comunidad PS4/PS3 + Steam + 1 cameo de tu clip local."""
    clips_locales = buscar_clips_locales()
    clips_yt = descargar_clips_youtube(busquedas_youtube, juegos_solicitados, max_clips=3)
    clips_comm = descargar_clips_comunidad_ps4(juegos_solicitados, max_clips=3)
    clips_steam = descargar_gameplay_steam_respaldo(juegos_solicitados, max_clips=4) if (len(clips_yt) + len(clips_comm)) < 4 else []

    externos = clips_yt + clips_comm + clips_steam
    random.shuffle(externos)
    mezcla = []

    if externos:
        mezcla.extend(externos[:2])
        if clips_locales:
            mezcla.append(random.choice(clips_locales))
        mezcla.extend(externos[2:5])
        print(f"Montaje listo: {len(clips_yt)} YouTube + {len(clips_comm)} Comunidad + {len(clips_steam)} Steam + cameo local.")
        return mezcla

    if clips_locales:
        return clips_locales

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

def construir_fondo_dinamico_con_flashes(duracion_objetivo, lista_recursos):
    secuencia = []
    flashes = []
    tiempo_acumulado = 0.0
    clips_abiertos = []

    pool = [r for r in lista_recursos if os.path.exists(r)]
    if not pool:
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), [], clips_abiertos

    indice = 0
    errores = 0

    while tiempo_acumulado < duracion_objetivo and errores < len(pool) * 2:
        ruta = pool[indice % len(pool)]
        indice += 1
        dur_corte = min(random.uniform(1.9, 2.3), duracion_objetivo - tiempo_acumulado)
        if dur_corte <= 0.15:
            break

        try:
            if ruta.lower().endswith((".jpg", ".jpeg", ".png")):
                base = ImageClip(ruta).set_duration(dur_corte)
                base = ajustar_a_vertical_hd(base, 720, 1280)
                sub = base.resize(lambda t, d=dur_corte: 1.0 + 0.07 * (t / max(0.1, d))).set_position(("center", "center"))
                clips_abiertos.append(base)
            else:
                v = VideoFileClip(ruta).without_audio()
                clips_abiertos.append(v)

                ciclo = indice // len(pool)
                offset_ciclo = (ciclo * 2.4) % max(0.5, v.duration - dur_corte)
                max_start = max(0.0, v.duration - dur_corte - 0.1)
                start_t = min(max_start, offset_ciclo)

                raw_sub = v.subclip(start_t, min(v.duration, start_t + dur_corte))
                raw_sub = ajustar_a_vertical_hd(raw_sub, 720, 1280)
                sub = raw_sub.resize(
                    lambda t, d=dur_corte: (1.08 - 0.06 * min(1.0, t / 0.25)) + 0.03 * (t / max(0.1, d))
                ).set_position(("center", "center"))

            if tiempo_acumulado > 0.2:
                flash = (
                    ColorClip(size=(720, 1280), color=(210, 245, 255))
                    .set_start(tiempo_acumulado)
                    .set_duration(0.12)
                    .set_opacity(0.45)
                )
                flashes.append(flash)

            secuencia.append(sub)
            tiempo_acumulado += sub.duration
            errores = 0
        except Exception as e:
            print(f"Error editando {ruta}: {e}")
            errores += 1

    if not secuencia:
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), [], clips_abiertos

    video_concat = concatenate_videoclips(secuencia, method="compose")
    return video_concat.subclip(0, min(duracion_objetivo, video_concat.duration)), flashes, clips_abiertos

def crear_animacion_intro_formato(formato_dia, duracion_total):
    w, h = 720, 1280
    archivos_temp = []
    clips_intro = []

    if formato_dia == "noticiero":
        banner = Image.new("RGBA", (660, 74), (0, 0, 0, 0))
        d = ImageDraw.Draw(banner)
        d.rounded_rectangle([0, 0, 660, 74], radius=18, fill=(220, 20, 60, 245), outline=(255, 230, 0, 255), width=4)
        try:
            f_news = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        except:
            f_news = ImageFont.load_default()
        d.text((330, 37), "ÚLTIMA HORA • NOVEDADES PS4 / PS3", fill=(255, 255, 255, 255), anchor="mm", font=f_news)

        ruta_b = "temp_intro_news.png"
        banner.save(ruta_b)
        archivos_temp.append(ruta_b)

        c_news = (
            ImageClip(ruta_b)
            .set_duration(3.5)
            .resize(lambda t: 1.0 + 0.04 * math.sin(t * 10))
            .set_position(("center", 335))
        )
        clips_intro.append(c_news)

    elif formato_dia == "top3":
        try:
            f_top = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
        except:
            f_top = ImageFont.load_default()

        puntos = [(1.5, "TOP #1"), (8.5, "TOP #2"), (15.5, "TOP #3")]
        for idx, (t_ini, texto) in enumerate(puntos):
            if t_ini + 4.0 < duracion_total:
                pill = Image.new("RGBA", (220, 66), (0, 0, 0, 0))
                d = ImageDraw.Draw(pill)
                d.rounded_rectangle([0, 0, 220, 66], radius=20, fill=(130, 25, 230, 240), outline=(255, 225, 0, 255), width=3)
                d.text((110, 33), texto, fill=(255, 230, 0, 255), anchor="mm", font=f_top)
                r_p = f"temp_top_{idx}.png"
                pill.save(r_p)
                archivos_temp.append(r_p)

                c_p = (
                    ImageClip(r_p)
                    .set_start(t_ini)
                    .set_duration(4.0)
                    .set_position((465, 155))
                )
                clips_intro.append(c_p)

    else:
        dur_coins = 2.8
        random.seed(42)
        particulas = [
            {
                "x": random.uniform(30, w - 30),
                "y0": random.uniform(-450, 200),
                "vy": random.uniform(480, 820),
                "vx": random.uniform(-60, 60),
                "radio": random.randint(18, 34),
                "fase": random.uniform(0, 6.28),
                "vel_giro": random.uniform(6, 14),
                "es_moneda": random.random() > 0.35
            }
            for _ in range(26)
        ]
        cache = {"t_key": -1, "rgb": None, "mask": None}

        def render_t(t):
            t_key = int(t * 24)
            if cache["t_key"] == t_key:
                return cache["rgb"], cache["mask"]

            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            alpha_global = int(255 * min(1.0, max(0.0, (dur_coins - t) / 0.5)))

            for p in particulas:
                cx = p["x"] + p["vx"] * t + 18 * math.sin(t * 4 + p["fase"])
                cy = p["y0"] + p["vy"] * t
                if cy < -50 or cy > h + 50:
                    continue
                r = p["radio"]
                if p["es_moneda"]:
                    escala_x = max(0.22, abs(math.cos(t * p["vel_giro"] + p["fase"])))
                    rx = int(r * escala_x)
                    draw.ellipse([cx - rx, cy - r, cx + rx, cy + r], fill=(255, 210, 0, alpha_global), outline=(255, 250, 180, alpha_global), width=3)
                else:
                    s = int(r * 0.85)
                    draw.polygon(
                        [(cx, cy - s), (cx + s // 3, cy - s // 3), (cx + s, cy),
                         (cx + s // 3, cy + s // 3), (cx, cy + s), (cx - s // 3, cy + s // 3),
                         (cx - s, cy), (cx - s // 3, cy - s // 3)],
                        fill=(120, 245, 255, alpha_global)
                    )

            arr = np.array(img)
            cache["t_key"] = t_key
            cache["rgb"] = arr[:, :, :3]
            cache["mask"] = arr[:, :, 3].astype(np.float64) / 255.0
            return cache["rgb"], cache["mask"]

        clip_rgb = VideoClip(lambda t: render_t(t)[0], duration=dur_coins)
        clip_mask = VideoClip(lambda t: render_t(t)[1], duration=dur_coins, ismask=True)
        clips_intro.append(clip_rgb.set_mask(clip_mask).set_duration(dur_coins))

    return clips_intro, archivos_temp

def encontrar_foto_creador():
    for nombre in ["walfedw.jpg", "walfedw.png", "flyer.png", "flyer.jpg"]:
        if os.path.exists(nombre):
            return nombre
    return None

def crear_stickers_animados_creador(duracion_total):
    ruta_foto = encontrar_foto_creador()
    if not ruta_foto:
        return [], []

    archivos_temp = []
    clips_stickers = []

    try:
        foto_orig = Image.open(ruta_foto).convert("RGB")
        w, h = foto_orig.size
        lado = min(w, h)
        left = (w - lado) // 2
        top = max(0, int((h - lado) * 0.25))
        cuadro = foto_orig.crop((left, top, left + lado, top + lado))

        tam_avatar = 148
        resample = getattr(Image, "Resampling", Image).LANCZOS
        avatar_img = cuadro.resize((tam_avatar, tam_avatar), resample)

        mask_circ = Image.new("L", (tam_avatar, tam_avatar), 0)
        ImageDraw.Draw(mask_circ).ellipse([4, 4, tam_avatar - 4, tam_avatar - 4], fill=255)

        badge = Image.new("RGBA", (tam_avatar + 16, tam_avatar + 36), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(badge)
        b_draw.ellipse([2, 2, tam_avatar + 14, tam_avatar + 14], fill=(0, 220, 255, 255))
        badge.paste(avatar_img, (8, 8), mask_circ)
        b_draw.rounded_rectangle([14, tam_avatar - 8, tam_avatar + 2, tam_avatar + 22], radius=10, fill=(235, 30, 110, 255))
        try:
            f_tag = ImageFont.truetype("DejaVuSans-Bold.ttf", 17)
        except:
            f_tag = ImageFont.load_default()
        b_draw.text(((tam_avatar + 16) // 2, tam_avatar + 7), "WALFEDW • PS4", fill=(255, 255, 255, 255), anchor="mm", font=f_tag)

        ruta_badge = "temp_avatar_badge.png"
        badge.save(ruta_badge)
        archivos_temp.append(ruta_badge)

        clip_avatar = (
            ImageClip(ruta_badge)
            .set_duration(duracion_total)
            .set_position(lambda t: (26, int(138 + 8 * math.sin(t * 3.5))))
        )
        clips_stickers.append(clip_avatar)

        tam_pop = 230
        pop_img = cuadro.resize((tam_pop, tam_pop), resample)
        mask_pop = Image.new("L", (tam_pop, tam_pop), 0)
        ImageDraw.Draw(mask_pop).rounded_rectangle([0, 0, tam_pop, tam_pop], radius=36, fill=255)

        pop_card = Image.new("RGBA", (tam_pop + 16, tam_pop + 16), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(pop_card)
        p_draw.rounded_rectangle([0, 0, tam_pop + 16, tam_pop + 16], radius=40, fill=(255, 225, 0, 255))
        pop_card.paste(pop_img, (8, 8), mask_pop)

        ruta_pop = "temp_popup_creator.png"
        pop_card.save(ruta_pop)
        archivos_temp.append(ruta_pop)

        for t_inicio in [3.8, 17.5]:
            if t_inicio + 2.8 < duracion_total:
                c_pop = (
                    ImageClip(ruta_pop)
                    .set_start(t_inicio)
                    .set_duration(2.8)
                    .resize(lambda t: max(0.3, 1.0 - 0.35 * math.exp(-8 * t) * math.cos(16 * t)))
                    .set_position(("center", 545))
                )
                clips_stickers.append(c_pop)

    except Exception as e:
        print(f"Advertencia stickers creador: {e}")

    return clips_stickers, archivos_temp

def crear_emoji_reaccion_animado(duracion_total):
    size = 86
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([4, 4, size - 4, size - 4], fill=(255, 215, 0, 255), outline=(255, 255, 255, 255), width=3)
    draw.rounded_rectangle([14, 26, 41, 43], radius=5, fill=(15, 20, 35, 255))
    draw.rounded_rectangle([45, 26, 72, 43], radius=5, fill=(15, 20, 35, 255))
    draw.line([(39, 31), (47, 31)], fill=(15, 20, 35, 255), width=4)
    draw.arc([24, 38, 62, 68], start=15, end=165, fill=(15, 20, 35, 255), width=5)

    ruta_emoji = "temp_emoji_cool.png"
    img.save(ruta_emoji)

    clip_emoji = (
        ImageClip(ruta_emoji)
        .set_duration(duracion_total)
        .set_position(lambda t: (605, int(1038 - abs(math.sin(t * 4.8)) * 18)))
    )
    return clip_emoji, ruta_emoji

def crear_overlay_marca_persistente(duracion, etiqueta_formato="FLASHEO PS4 Y PS3 • TAMBIÉN PS5"):
    w, h = 720, 1280
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        f_brand = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        f_sub = ImageFont.truetype("DejaVuSans-Bold.ttf", 19)
    except:
        f_brand = f_sub = ImageFont.load_default()

    draw.rounded_rectangle([55, 48, 665, 122], radius=24, fill=(8, 15, 30, 220), outline=(0, 210, 255, 255), width=3)
    draw.text((360, 74), "@WALFEDW • WALFEDW SERVICES", fill=(255, 255, 255, 255), anchor="mm", font=f_brand)
    draw.text((360, 102), etiqueta_formato, fill=(0, 220, 255, 255), anchor="mm", font=f_sub)

    draw.rounded_rectangle([90, 1140, 630, 1192], radius=18, fill=(8, 15, 30, 215), outline=(255, 225, 0, 235), width=2)
    draw.text((360, 1166), "CONSULTA TU VERSIÓN • WA: 914 899 697", fill=(255, 230, 0, 255), anchor="mm", font=f_sub)

    ruta_png = "temp_brand_overlay.png"
    img.save(ruta_png)
    return ImageClip(ruta_png).set_duration(duracion), ruta_png

def renderizar_frame_subtitulo(palabras_grupo, indice_activo, idx_frame):
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
                .resize(lambda t: 1.06 - 0.06 * min(1.0, t / 0.12))
                .set_position(("center", 820))
            )
            clips_subs.append(clip_txt)

    return clips_subs, archivos_temp

def generar_sfx_animaciones(duracion_total):
    sr = 44100
    n_samples = int(duracion_total * sr)
    audio = np.zeros((n_samples, 2), dtype=np.float64)

    notas_coin = [(0.05, 987.77), (0.14, 1318.51), (0.24, 1567.98), (0.35, 2093.00)]
    for t0, freq in notas_coin:
        i0 = int(t0 * sr)
        dur_n = int(0.28 * sr)
        if i0 + dur_n < n_samples:
            t_arr = np.linspace(0, 0.28, dur_n)
            env = np.exp(-12 * t_arr)
            onda = 0.22 * env * (np.sin(2 * np.pi * freq * t_arr) + 0.3 * np.sin(4 * np.pi * freq * t_arr))
            audio[i0:i0 + dur_n, 0] += onda
            audio[i0:i0 + dur_n, 1] += onda

    for t_pop in [3.8, 17.5]:
        i0 = int(t_pop * sr)
        dur_p = int(0.14 * sr)
        if i0 + dur_p < n_samples:
            t_arr = np.linspace(0, 0.14, dur_p)
            freq_sweep = 320 + 680 * (t_arr / 0.14)
            env = np.exp(-18 * t_arr)
            onda = 0.28 * env * np.sin(2 * np.pi * freq_sweep * t_arr)
            audio[i0:i0 + dur_p, 0] += onda
            audio[i0:i0 + dur_p, 1] += onda

    audio = np.clip(audio, -0.9, 0.9)
    return AudioArrayClip(audio, fps=sr).set_duration(duracion_total)

def obtener_clip_flyer_cierre(duracion_flyer=4.0):
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
    return clip_img.resize(lambda t: 1.04 - 0.04 * (t / duracion_flyer)).set_position(("center", "center"))

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
    except Exception:
        pass
    return None

def crear_video(datos_guion, archivo_salida="noticia_tiktok.mp4"):
    formato_dia = datos_guion.get("formato_dia", "noticiero")
    etiqueta_formato = datos_guion.get("etiqueta_formato", "FLASHEO PS4 Y PS3 • TAMBIÉN PS5")
    locucion = datos_guion.get(
        "locucion_completa",
        "¿Tienes una PS4 o PS3 en casa y sigues pagando carísimo por cada juego? En Walfedw Services yo me encargo de flashear tu consola e instalarte los mejores títulos."
    )
    juegos_visuales = datos_guion.get(
        "juegos_visuales",
        ["God of War Ragnarok", "Ghost of Tsushima", "Red Dead Redemption 2", "Grand Theft Auto V"]
    )
    busquedas_youtube = datos_guion.get(
        "busquedas_youtube",
        ["PS4 GoldHEN menu showcase"] + [f"{j} PS4 gameplay" for j in juegos_visuales]
    )

    print(f"1. Generando voz y tiempos para formato [{formato_dia.upper()}]...")
    audio_voz_path = "temp_voz_viral.mp3"
    tiempos_palabras = asyncio.run(generar_audio_con_tiempos(locucion, audio_voz_path))
    audio_voz = AudioFileClip(audio_voz_path).volumex(1.25)

    duracion_escena_principal = max(27.0, audio_voz.duration + 0.6)

    print("2. Extrayendo clips nuevos de YouTube, comunidad PS4/PS3 y gameplays...")
    lista_recursos = obtener_recursos_visuales(busquedas_youtube, juegos_visuales)
    video_broll, clips_flash, clips_abiertos = construir_fondo_dinamico_con_flashes(duracion_escena_principal, lista_recursos)

    print("3. Aplicando animación de intro según el día, avatar flotante, pop-ups y subtítulos...")
    clips_intro, temp_intro = crear_animacion_intro_formato(formato_dia, duracion_escena_principal)
    stickers_creador, temp_stickers = crear_stickers_animados_creador(duracion_escena_principal)
    emoji_animado, temp_emoji = crear_emoji_reaccion_animado(duracion_escena_principal)
    overlay_marca, ruta_marca_png = crear_overlay_marca_persistente(duracion_escena_principal, etiqueta_formato)
    clips_subs, archivos_subs_temp = crear_subtitulos_capcut(tiempos_palabras, locucion, audio_voz.duration)

    capas_escena = (
        [video_broll]
        + clips_flash
        + clips_intro
        + [overlay_marca]
        + stickers_creador
        + [emoji_animado]
        + clips_subs
    )

    escena_principal = CompositeVideoClip(capas_escena, size=(720, 1280)).set_audio(audio_voz)

    print("4. Cerrando con tu flyer oficial de GitHub (4.0s)...")
    clip_flyer = obtener_clip_flyer_cierre(duracion_flyer=4.0)
    video_completo = concatenate_videoclips([escena_principal, clip_flyer], method="compose")

    print("5. Mezclando música gamer + efectos de sonido (SFX)...")
    total_dur = video_completo.duration
    pistas_audio = []
    if video_completo.audio is not None:
        pistas_audio.append(video_completo.audio.set_duration(total_dur))

    pistas_audio.append(generar_sfx_animaciones(total_dur))

    bgm_path = descargar_musica_fondo()
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path)
            if bgm.duration < total_dur:
                n_loops = int(total_dur / bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * n_loops)
            bgm = bgm.subclip(0, total_dur).volumex(0.11).set_duration(total_dur)
            pistas_audio.append(bgm)
        except Exception as e:
            print(f"Advertencia BGM: {e}")

    audio_final = CompositeAudioClip(pistas_audio).set_duration(total_dur)
    video_completo = video_completo.set_audio(audio_final)

    print(f"6. Exportando MP4 editado ({total_dur:.1f} segundos)...")
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
        [audio_voz_path, "temp_bg_black.png", "temp_flyer_github_card.png", ruta_marca_png, temp_emoji]
        + temp_intro
        + temp_stickers
        + archivos_subs_temp
        + glob.glob("temp_yt_*.mp4")
        + glob.glob("temp_comm_*.mp4")
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
