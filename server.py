import os
import time
import hmac
import base64
import hashlib
import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

API_KEY = os.getenv("API_KEY", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
PASSPHRASE = os.getenv("PASSPHRASE", "").strip()

BASE_URL = "https://www.okx.com"
autopilot_active = False

def get_okx_server_time_diff():
    """Sincronizzazione orario ultra-robusta con i server OKX"""
    try:
        # Usiamo un timeout rapido e verifichiamo la risposta
        response = requests.get(f"{BASE_URL}/api/v5/public/time", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                server_time_ms = int(data['data'][0]['ts'])
                local_time_ms = int(time.time() * 1000)
                diff = server_time_ms - local_time_ms
                print(f"Sincronizzazione OKX riuscita. Scarto orario: {diff} ms")
                return diff
    except Exception as e:
        print(f"Avviso sync orario fallito: {e}. Uso fallback locale.")
    return 0

def get_signed_headers(method, request_path, body=""):
    """Genera la firma con correzione fissa di sicurezza per evitare scadenza timestamp"""
    time_diff = get_okx_server_time_diff()
    # Aggiungiamo un piccolo buffer di tolleranza di 500ms indietro per evitare 'Timestamp request expired'
    timestamp = str(int(time.time() * 1000) + time_diff - 500)
    
    message = timestamp + method.upper() + request_path + body
    
    mac = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    signature = base64.b64encode(mac.digest()).decode('utf-8')
    
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/balance", methods=["GET"])
def check_balance():
    endpoint = "/api/v5/account/balance"
    headers = get_signed_headers("GET", endpoint)
    url = BASE_URL + endpoint
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Risposta Saldo OKX Status: {response.status_code}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "-1", "msg": str(e)}), 500

@app.route("/api/autopilot", methods=["POST"])
def toggle_autopilot():
    global autopilot_active
    data = request.get_json()
    autopilot_active = data.get("active", False)
    print(f"--- Autopilot impostato a: {autopilot_active} ---")
    return jsonify({"status": "success", "autopilot": autopilot_active})

@app.route("/api/trade", methods=["POST"])
def execute_trade():
    """Invia un ordine reale a mercato su OKX (es. COMPRA / VENDI)"""
    data = request.get_json()
    action = data.get("action", "BUY")
    symbol = data.get("symbol", "BTC-USDT")
    
    endpoint = "/api/v5/trade/order"
    
    # Corpo della richiesta per ordine a mercato (Market) su OKX
    # (Esegue l'ordine immediato sul conto reale)
    payload = {
        "instId": symbol,
        "tdMode": "cash",  # Modalità contanti / spot
        "side": action.lower(), # 'buy' o 'sell'
        "ordType": "market",
        "sz": "0.0001"  # Quantità minima di test in BTC (regolabile)
    }
    
    import json
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    
    try:
        response = requests.post(BASE_URL + endpoint, headers=headers, data=body_str, timeout=10)
        print(f"Risposta Ordine OKX: {response.text}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "-1", "msg": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
