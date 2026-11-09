import time
import datetime
import base64
import hmac
import hashlib
import json
import threading
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_KEY = "e059ce24-96a8-445d-b374-bfad44938d9c"
SECRET_KEY = "1BFCDA6FEF287CAC00B8D96FD222EF4A"
PASSPHRASE = "King_939625"

BASE_URL = "https://my.okx.com"

# Stato globale dell'Autopilot
autopilot_state = {"active": False}

def get_okx_time():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def get_sign(timestamp, method, request_path, body=""):
    message = timestamp + method.upper() + request_path + body
    mac = hmac.new(
        bytes(SECRET_KEY, encoding='utf-8'),
        bytes(message, encoding='utf-8'),
        digestmod=hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode('utf-8')

def get_signed_headers(method, request_path, body=""):
    timestamp = get_okx_time()
    signature = get_sign(timestamp, method, request_path, body)
    return {
        "OK-ACCESS-KEY": API_KEY,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "x-simulated-trading": "0"
    }

# Funzione in background che gira continuamente quando l'Autopilot è attivo
def autopilot_background_worker():
    while True:
        if autopilot_state["active"]:
            try:
                print("🤖 Autopilot in esecuzione: controllo mercato BTC-USDC...")
                # Qui puoi inserire la logica di controllo o test periodico (es. ogni 30 secondi)
                # Ad esempio, verifica del prezzo o esecuzione automatica condizionata
            except Exception as e:
                print(f"Errore nel worker dell'Autopilot: {e}")
        time.sleep(30) # Controlla ogni 30 secondi

# Avvia il thread in background all'avvio del server
worker_thread = threading.Thread(target=autopilot_background_worker, daemon=True)
worker_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/balance", methods=["GET"])
def check_balance():
    endpoint = "/api/v5/account/balance?ccy=USDC"
    headers = get_signed_headers("GET", endpoint)
    url = BASE_URL + endpoint
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/positions", methods=["GET"])
def get_positions():
    endpoint = "/api/v5/trade/orders-pending?instType=SPOT"
    headers = get_signed_headers("GET", endpoint)
    url = BASE_URL + endpoint
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/close-positions", methods=["POST"])
def close_positions():
    endpoint = "/api/v5/trade/cancel-batch-orders"
    headers_get = get_signed_headers("GET", "/api/v5/trade/orders-pending?instId=BTC-USDC")
    try:
        pending_res = requests.get(BASE_URL + "/api/v5/trade/orders-pending?instId=BTC-USDC", headers=headers_get, timeout=10).json()
        orders = pending_res.get("data", [])
        
        if not orders:
            return jsonify({"code": "0", "msg": "Nessun ordine aperto da chiudere."})
        
        cancel_payload = [{"instId": o["instId"], "ordId": o["ordId"]} for o in orders]
        body_str = json.dumps(cancel_payload)
        headers_post = get_signed_headers("POST", endpoint, body_str)
        
        response = requests.post(BASE_URL + endpoint, headers=headers_post, data=body_str, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/buy", methods=["POST"])
def buy_crypto():
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": "BTC-USDC",
        "tdMode": "cash",
        "side": "buy",
        "ordType": "market",
        "sz": request.json.get("size", "0.001")
    }
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    url = BASE_URL + endpoint
    try:
        response = requests.post(url, headers=headers, data=body_str, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/sell", methods=["POST"])
def sell_crypto():
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": "BTC-USDC",
        "tdMode": "cash",
        "side": "sell",
        "ordType": "market",
        "sz": request.json.get("size", "0.001")
    }
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    url = BASE_URL + endpoint
    try:
        response = requests.post(url, headers=headers, data=body_str, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/autopilot", methods=["POST"])
def autopilot():
    data = request.json or {}
    action = data.get("action", False)
    autopilot_state["active"] = action
    
    msg = "Autopilot attivato e in esecuzione in background." if action else "Autopilot disattivato."
    
    return jsonify({
        "status": "success", 
        "autopilot": "active" if action else "inactive",
        "msg": msg
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
