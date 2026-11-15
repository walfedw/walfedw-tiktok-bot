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

# Imágenes HD verificadas de respaldo si la carpeta clips/ está vacía
IMAGENES_RESPALDO_HD = [
    "https://cdn.akamai.steamstatic.com/steam/apps/2322010/header.jpg",
    "https://cdn.akamai.steamstatic.com/steam/apps/1174180/header.jpg",
    "https://cdn.akamai.steamstatic.com/steam/apps/1817070/header.jpg",
    "https://cdn.akamai.steamstatic.com/steam/apps/2215430/header.jpg",
    "https://images.unsplash.com/photo-1507457379470-08b800bebc67?w=1080&h=1920&fit=crop"
]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?áéíóúÁÉÍÓÚñÑ\-]', '', texto).strip()

async def generar_audio_con_tiempos(texto, archivo_salida):
    """Genera el MP3 de voz y captura el timestamp exacto de cada palabra."""
    texto_limpio = limpiar_texto(texto)
    for voz in VOCES:
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
                return tiempos_palabras
        except Exception as e:
            print(f"Advertencia con voz {voz}: {e}")
    raise RuntimeError("No se pudo generar el audio de locución.")

def obtener_recursos_visuales():
    """Busca clips .mp4/.mov o imágenes en clips/. Si está vacía, descarga imágenes HD de respaldo."""
    extensiones = ("clips/*.mp4", "clips/*.MP4", "clips/*.mov", "clips/*.MOV", "clips/*.jpg", "clips/*.png")
    archivos_locales = []
    for ext in extensiones:
        archivos_locales.extend(glob.glob(ext))
    archivos_locales = sorted(archivos_locales)

    if archivos_locales:
        print(f"Usando {len(archivos_locales)} archivos reales encontrados en clips/.")
        return archivos_locales

    print("Carpeta clips/ vacía. Descargando recursos HD de respaldo...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    descargados = []
    for idx, url in enumerate(IMAGENES_RESPALDO_HD):
        nombre = f"temp_stock_{idx}.jpg"
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200 and len(res.content) > 3000:
                with open(nombre, "wb") as f:
                    f.write(res.content)
                descargados.append(nombre)
        except Exception as e:
            print(f"Error descargando respaldo {idx}: {e}")
    return descargados

def ajustar_a_vertical(clip, target_w=720, target_h=1280):
    """Recorta y escala cualquier video o imagen a 720x1280 sin deformar."""
    w, h = clip.size
    if (w / h) > (target_w / target_h):
        clip = clip.resize(height=target_h)
    else:
        clip = clip.resize(width=target_w)
    return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)

def construir_fondo_dinamico(duracion_objetivo, lista_recursos):
    """Arma una secuencia de cortes rápidos de ~2.0 segundos cada uno."""
    secuencia = []
    tiempo_acumulado = 0.0
    clips_abiertos = []

    pool = [r for r in lista_recursos if os.path.exists(r)]
    if not pool:
        print("Sin recursos externos disponibles. Generando fondo oscuro de emergencia...")
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), clips_abiertos

    random.shuffle(pool)
    indice = 0
    errores_seguidos = 0

    while tiempo_acumulado < duracion_objetivo and errores_seguidos < len(pool) * 2:
        ruta = pool[indice % len(pool)]
        indice += 1
        dur_corte = min(random.uniform(1.8, 2.3), duracion_objetivo - tiempo_acumulado)
        if dur_corte <= 0.15:
            break

        try:
            if ruta.lower().endswith((".jpg", ".jpeg", ".png")):
                img_clip = ImageClip(ruta).set_duration(dur_corte)
                img_clip = ajustar_a_vertical(img_clip, 720, 1280)
                sub = img_clip.resize(lambda t, d=dur_corte: 1.0 + 0.08 * (t / d)).set_position(("center", "center"))
                clips_abiertos.append(img_clip)
            else:
                v = VideoFileClip(ruta).without_audio()
                clips_abiertos.append(v)
                max_start = max(0.0, v.duration - dur_corte - 0.1)
                start_t = random.uniform(0.0, max_start) if max_start > 0 else 0.0
                sub = v.subclip(start_t, min(v.duration, start_t + dur_corte))
                sub = ajustar_a_vertical(sub, 720, 1280)

            secuencia.append(sub)
            tiempo_acumulado += sub.duration
            errores_seguidos = 0
        except Exception as e:
            print(f"Error procesando recurso {ruta}: {e}")
            errores_seguidos += 1

    if not secuencia:
        img_negra = Image.new("RGB", (720, 1280), (10, 14, 24))
        img_negra.save("temp_bg_black.png")
        return ImageClip("temp_bg_black.png").set_duration(duracion_objetivo), clips_abiertos

    video_concat = concatenate_videoclips(secuencia, method="compose")
    return video_concat.subclip(0, min(duracion_objetivo, video_concat.duration)), clips_abiertos

def renderizar_frame_subtitulo(palabras_grupo, indice_activo, idx_frame):
    """Dibuja subtítulos estilo CapCut: texto blanco grueso + caja rosa neón en la palabra activa."""
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
    """Sincroniza grupos de 3 palabras con caja saltarina palabra por palabra."""
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
                .set_position(("center", 780))
            )
            clips_subs.append(clip_txt)

    return clips_subs, archivos_temp

def obtener_clip_flyer_cierre(duracion_flyer=2.8):
    """Carga flyer.jpg a pantalla completa con zoom suave al final del video."""
    for candidato in ["flyer.jpg", "flyer.png", "walfedw_flyer.jpg", "walfedw.jpg"]:
        if os.path.exists(candidato):
            print(f"Integrando flyer final oficial: {candidato}")
            clip_img = ImageClip(candidato).set_duration(duracion_flyer)
            clip_img = ajustar_a_vertical(clip_img, 720, 1280)
            return clip_img.resize(lambda t: 1.05 - 0.05 * (t / duracion_flyer)).set_position(("center", "center"))

    img = Image.new("RGB", (720, 1280), (12, 18, 32))
    draw = ImageDraw.Draw(img)
    try:
        f_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
        f_med = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except:
        f_big = f_med = ImageFont.load_default()
    draw.text((360, 520), "WALFEDW SERVICES", fill=(0, 210, 255), anchor="mm", font=f_big)
    draw.text((360, 620), "FLASHEO PS3 • PS4 • PS5", fill=(255, 220, 0), anchor="mm", font=f_med)
    draw.text((360, 720), "WHATSAPP: 914 899 697", fill=(255, 255, 255), anchor="mm", font=f_med)
    draw.text((360, 790), "IG: @walfedw23", fill=(255, 255, 255), anchor="mm", font=f_med)
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
        "Esa PS4 ahí sentada puede hacer mucho más de lo que crees. Flashéala en Walfedw para obtener miles de juegos sin costos elevados. Contáctanos hoy mismo."
    )

    print("1. Generando voz con sincronización palabra por palabra...")
    audio_voz_path = "temp_voz_viral.mp3"
    tiempos_palabras = asyncio.run(generar_audio_con_tiempos(locucion, audio_voz_path))
    audio_voz = AudioFileClip(audio_voz_path)
    duracion_voz = audio_voz.duration

    print("2. Preparando cortes rápidos visuales...")
    lista_recursos = obtener_recursos_visuales()
    video_broll, clips_abiertos = construir_fondo_dinamico(duracion_voz, lista_recursos)

    print("3. Renderizando subtítulos dinámicos estilo CapCut...")
    clips_subs, archivos_subs_temp = crear_subtitulos_capcut(tiempos_palabras, locucion, duracion_voz)

    escena_principal = CompositeVideoClip([video_broll] + clips_subs, size=(720, 1280)).set_audio(audio_voz)

    print("4. Añadiendo flyer comercial de cierre (2.8s)...")
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

    for f in [audio_voz_path, "temp_bg_black.png", "temp_flyer_fallback.png"] + archivos_subs_temp:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass
    for stock in glob.glob("temp_stock_*"):
        try:
            os.remove(stock)
        except:
            pass

    return archivo_salida
