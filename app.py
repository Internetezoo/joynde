import asyncio
import nest_asyncio
import logging
import os
import json
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright

# Engedélyezzük az aszinkron futást Flask alatt
nest_asyncio.apply()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- JOYN SZŰRŐ FÜGGVÉNY ---
def is_important_joyn_url(url):
    # Ezekre a kulcsszavakra vadászunk a Joyn hálózatában
    targets = ["m3u8", "mpd", "iocproactor", "playback", "license", "manifest"]
    return any(x in url.lower() for x in targets)

# --- PLAYWRIGHT SNIFFER (A LÉNYEG) ---
async def run_joyn_sniffer(target_url):
    captured_links = []
    
    async with async_playwright() as p:
        # no-sandbox mód a szerveres futtatáshoz
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Figyeljük a hálózati kéréseket
        async def handle_request(request):
            url = request.url
            if is_important_joyn_url(url):
                captured_links.append({
                    "method": request.method,
                    "url": url,
                    "type": request.resource_type
                })

        page.on("request", handle_request)

        try:
            logging.info(f"🌐 Joyn oldal megnyitása: {target_url}")
            # Networkidle-re várunk, hogy a lejátszó is betöltsön
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Várunk 10 másodpercet, hogy a stream linkek biztosan megérkezzenek
            await asyncio.sleep(10)
            
        except Exception as e:
            logging.error(f"❌ Playwright hiba: {e}")
        finally:
            await browser.close()
            
    return captured_links

# --- FLASK VÉGPONT ---
@app.route('/scrape', methods=['GET'])
def scrape():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "Hiányzó 'url' paraméter!"}), 400

    logging.info(f"🚀 Indítás: {target_url}")
    
    # Aszinkron loop futtatása
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        hits = loop.run_until_complete(run_joyn_sniffer(target_url))
        return jsonify({
            "status": "success",
            "hits_count": len(hits),
            "hits": hits
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        loop.close()

if __name__ == '__main__':
    # Render port kezelése
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
