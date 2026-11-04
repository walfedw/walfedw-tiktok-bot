import os
import asyncio
import re
import urllib.parse
import requests
import edge_tts
from playwright.sync_api import sync_playwright
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip

VOCES = ["es-MX-DarianNeural", "es-MX-JorgeNeural", "es-ES-AlvaroNeural"]

def limpiar_texto(texto):
    return re.sub(r'[^\w\s.,¡!¿?@#\-áéíóúÁÉÍÓÚñÑ]', '', texto).strip()

async def generar_audio(texto, archivo_salida="voz.mp3"):
    texto_procesar = limpiar_texto(texto)
    if not texto_procesar:
        texto_procesar = "Flasheo, liberación, catálogo de juegos y mantenimiento para PS3, PS4, PS5 y Switch en Walfedw."

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

def generar_escena_html(titulo, guion, codigo_pantalla, prompt_img):
    url_bg = descargar_url_imagen(prompt_img)
    
    html_content = f"""
    <!DOCTYPE html>
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
                filter: blur(10px) brightness(0.35);
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
                background: rgba(15, 23, 42, 0.75);
                border: 2px solid #00d2ff;
                border-radius: 20px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 0 25px rgba(0, 210, 255, 0.4);
                backdrop-filter: blur(12px);
            }}
            .brand {{ font-size: 38px; font-weight: 900; color: #00d2ff; letter-spacing: 2px; text-shadow: 0 0 12px #00d2ff; }}
            .sub-brand {{ font-size: 20px; color: #ffc800; font-weight: 700; margin-top: 6px; }}

            .main-card {{
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(0, 210, 255, 0.5);
                border-radius: 24px;
                padding: 30px;
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
                margin-bottom: 20px;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.8);
            }}
            .description {{ font-size: 23px; color: #cbd5e1; line-height: 1.45; font-weight: 400; }}

            .cta-box {{
                background: linear-gradient(135deg, #00d2ff 0%, #0072ff 100%);
                border-radius: 20px;
                padding: 22px;
                text-align: center;
                color: #0b0f19;
                box-shadow: 0 0 30px rgba(0, 210, 255, 0.6);
            }}
            .cta-title {{ font-size: 30px; font-weight: 900; letter-spacing: 1px; }}
            .cta-desc {{ font-size: 20px; font-weight: 800; margin-top: 4px; opacity: 0.95; }}
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
                    <span style="color:#f43f5e">console_config</span> {<br>
                      <span style="color:#38bdf8">mode</span>: <span style="color:#fde047">"Flasheada / HEN"</span>;<br>
                      <span style="color:#38bdf8">status</span>: <span style="color:#4ade80">"Juegos Desbloqueados"</span>;<br>
                    }
                </div>
                <div class="description">{guion[:220]}...</div>
            </div>

            <div class="cta-box">
                <div class="cta-title">PS3 • PS4 • PS5 • SWITCH</div>
                <div class="cta-desc">¡Escríbenos para Asesoría y Juegos!</div>
            </div>
        </div>
    </body>
    </html>
    """
    
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

def crear_video(guion_texto, titulo_texto, codigo_pantalla="", prompt_img="gaming console hardware", archivo_salida="noticia_tiktok.mp4"):
    print("1. Generando locución...")
    asyncio.run(generar_audio(guion_texto, "voz.mp3"))

    print("2. Generando render de pantalla HTML5/CSS3...")
    generar_escena_html(titulo_texto, guion_texto, codigo_pantalla, prompt_img)
    renderizar_html_a_imagen()

    print("3. Renderizando MP4...")
    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    clip_base = ImageClip("fondo_pantalla.png").set_duration(duracion)
    clip_animado = clip_base.resize(lambda t: 1 + 0.03 * (t / duracion))
    clip_animado = clip_animado.set_position(('center', 'center')).set_duration(duracion)

    video_final = CompositeVideoClip([clip_animado], size=(720, 1280)).set_audio(audio)

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
    return archivo_salida
