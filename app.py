import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
import os

app = Flask(__name__)

async def scrape_network(target_url):
    network_log = []
    
    async with async_playwright() as p:
        # A Renderen lévő Dockerben így kell indítani a böngészőt
        browser = await p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
        page = await browser.new_page()

        # Minden hálózati kérést elkapunk
        def handle_request(request):
            url = request.url
            # Csak a fontos dolgokat naplózzuk, hogy ne legyen túl nagy a válasz
            if any(x in url.lower() for x in ["m3u8", "mpd", "iocproactor", "playback", "license"]):
                network_log.append({"type": request.resource_type, "url": url})

        page.on("request", handle_request)

        try:
            # Oldal betöltése a Render német IP-jéről
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            # Várunk, hogy a lejátszó elinduljon és generálja a linkeket
            await asyncio.sleep(10) 
            
            html_content = await page.content()
            await browser.close()
            return {"status": "success", "hits": network_log, "html_preview": html_content[:500]}
        except Exception as e:
            await browser.close()
            return {"status": "error", "message": str(e)}

@app.route('/scrape')
def scrape():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Meghívjuk az aszinkron figyelőt
    result = asyncio.run(scrape_network(url))
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
