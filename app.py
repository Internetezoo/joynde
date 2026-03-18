from flask import Flask, request, jsonify
import cloudscraper
import os

app = Flask(__name__)

# JAVÍTÁS: Definiálunk egy böngészőt, hogy hitelesebb legyen a lekérés
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# ÚJ: Egy sima üdvözlő üzenet a főoldalra (teszteléshez)
@app.route('/')
def index():
    return "A Joyn Scraper API fut! Használd a /scrape?url=... végpontot."

@app.route('/scrape', methods=['GET'])
def scrape():
    target_url = request.args.get('url', 'https://www.joyn.de')
    
    try:
        # A timeoutot érdemes 20-ra emelni, mert a Joyn néha lassú
        response = scraper.get(target_url, timeout=20)
        
        return jsonify({
            "status": response.status_code,
            "url": target_url,
            "content": response.text[:10000] # Emeltem kicsit a limiten
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ez a rész tökéletes a Renderhez
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
