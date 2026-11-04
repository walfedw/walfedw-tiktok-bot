import feedparser
import requests

# Fuentes de Reddit y blogs especializados en consolas liberadas
FEEDS_REDDIT = [
    "https://www.reddit.com/r/ps4homebrew/hot.rss",
    "https://www.reddit.com/r/ps5homebrew/hot.rss",
    "https://www.reddit.com/r/ps3homebrew/hot.rss",
    "https://www.reddit.com/r/SwitchPirates/hot.rss",
    "https://wololo.net/feed/"
]

def obtener_noticias():
    noticias = []
    # Simular navegador para evitar bloqueos 429/403 de Reddit
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WalfedwBot/1.0"}

    for feed_url in FEEDS_REDDIT:
        try:
            res = requests.get(feed_url, headers=headers, timeout=15)
            if res.status_code == 200:
                parsed = feedparser.parse(res.content)
                for entry in parsed.entries[:5]:
                    titulo = entry.get('title', '')
                    resumen = entry.get('summary', entry.get('description', ''))
                    
                    if titulo and not any(n['titulo'] == titulo for n in noticias):
                        noticias.append({
                            "titulo": titulo,
                            "resumen": resumen,
                            "link": entry.get('link', '')
                        })
        except Exception as e:
            print(f"Error al leer feed {feed_url}: {e}")

    print(f"Total de temas recopilados de Reddit/Scene: {len(noticias)}")
    return noticias

if __name__ == "__main__":
    resultado = obtener_noticias()
    for i, n in enumerate(resultado[:5], 1):
        print(f"{i}. {n['titulo']}")
