from flask import Flask, request, jsonify
import cloudscraper
import os

app = Flask(__name__)
scraper = cloudscraper.create_scraper()

@app.route('/scrape', methods=['GET'])
def scrape():
    # Megadjuk az URL-t, amit le akarunk kérni (alapértelmezett a joyn.de)
    target_url = request.args.get('url', 'https://www.joyn.de')
    
    try:
        # A szerver belülről indítja a kérést
        response = scraper.get(target_url, timeout=15)
        
        # Visszaküldjük az eredményt
        return jsonify({
            "status": response.status_code,
            "url": target_url,
            "content": response.text[:5000]  # Csak az első 5000 karakter a teszthez
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # A Rendernek kell a PORT változó kezelése
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
