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
    """Sincronizzazione orario perfetta con i server OKX per evitare errori timestamp"""
    try:
        response = requests.get(f"{BASE_URL}/api/v5/public/time", timeout=5)
        if response.status_code == 200:
            server_time_ms = int(response.json()['data'][0]['ts'])
            local_time_ms = int(time.time() * 1000)
            return server_time_ms - local_time_ms
    except Exception as e:
        print(f"Errore sync orario: {e}")
    return 0

def get_signed_headers(method, request_path, body=""):
    time_diff = get_okx_server_time_diff()
    timestamp = str(int(time.time() * 1000) + time_diff)
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
    try:
        response = requests.get(BASE_URL + endpoint, headers=headers, timeout=10)
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
    data = request.get_json()
    action = data.get("action")
    print(f"--- Richiesta ordine manuale: {action} ---")
    # Qui si collegherà l'endpoint OKX /api/v5/trade/order
    return jsonify({"status": "success", "action": action, "msg": "Ordine inviato al server"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
