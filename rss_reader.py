import feedparser
import ssl

# Desactivar verificación estricta de SSL si algún feed da problemas
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# Feeds de la scene, firmware y noticias de consolas
FEEDS_RSS = [
    "https://wololo.net/feed/",
    "https://blog.es.playstation.com/feed/",
    "https://www.nintenderos.com/feed/",
    "https://vandal.elespanol.com/xml.cgi",
    "https://news.google.com/rss/search?q=PS5+PS4+PS3+Switch+firmware+scene+when:7d&hl=es-419&gl=CL&ceid=CL:es-419"
]

def obtener_noticias():
    todas_las_noticias = []

    for url in FEEDS_RSS:
        try:
            feed = feedparser.parse(url)
            for entrada in feed.entries[:4]:  # Tomar hasta 4 noticias por fuente
                titulo = entrada.get('title', '')
                resumen = entrada.get('summary', entrada.get('description', ''))
                enlace = entrada.get('link', '')

                if titulo:
                    todas_las_noticias.append({
                        "titulo": titulo,
                        "resumen": resumen[:300], # Limitar tamaño
                        "enlace": enlace
                    })
        except Exception as e:
            print(f"Advertencia: No se pudo leer el feed {url}. Error: {e}")

    return todas_las_noticias

if __name__ == "__main__":
    noticias = obtener_noticias()
    print(f"Total noticias recolectadas: {len(noticias)}")
    for i, n in enumerate(noticias[:3], 1):
        print(f"{i}. {n['titulo']}")
