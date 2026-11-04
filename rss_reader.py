import feedparser
import urllib.parse

# Fuentes RSS de la Scene, Homebrew y rastreadores de noticias sobre NanospeedGamer y TheWizWiki
FEEDS_RSS = [
    # Noticias directas de Wololo (escena PS4/PS5/Switch/PS3)
    "https://wololo.net/feed/",
    
    # Rastreador de publicaciones/menciones de NanospeedGamer y GoldHEN
    "https://news.google.com/rss/search?q=" + urllib.parse.quote("NanospeedGamer OR GoldHEN OR PS4 HEN") + "&hl=es-419&gl=PE&ceid=PE:es-419",
    
    # Rastreador de novedades de TheWizWiki y Scene PS5/Switch
    "https://news.google.com/rss/search?q=" + urllib.parse.quote("TheWizWiki OR PS5 Jailbreak OR Atmosphere Switch") + "&hl=es-419&gl=PE&ceid=PE:es-419",
    
    # Novedades generales de consolas y liberación
    "https://news.google.com/rss/search?q=" + urllib.parse.quote("flasheo PS4 OR libera PS5 OR HEN PS3") + "&hl=es-419&gl=PE&ceid=PE:es-419"
]

def obtener_noticias():
    noticias = []
    
    for feed_url in FEEDS_RSS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:5]:
                titulo = entry.get('title', '')
                resumen = entry.get('summary', entry.get('description', ''))
                
                # Evitar duplicados
                if not any(n['titulo'] == titulo for n in noticias):
                    noticias.append({
                        "titulo": titulo,
                        "resumen": resumen,
                        "link": entry.get('link', '')
                    })
        except Exception as e:
            print(f"Error al leer feed {feed_url}: {e}")

    print(f"Total de noticias/novedades recolectadas: {len(noticias)}")
    return noticias

if __name__ == "__main__":
    resultado = obtener_noticias()
    for i, n in enumerate(resultado[:5], 1):
        print(f"{i}. {n['titulo']}")
