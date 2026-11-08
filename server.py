import os
import hmac
import base64
import hashlib
import json
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

API_KEY = "c3f9bfde-c611-4972-a203-79c5aa27cd88"
SECRET_KEY = "19091AD9B5B41792FE066C79DF6B37BB"
PASSPHRASE = "King_939625"

BASE_URL = "https://my.okx.com"
autopilot_active = False

def get_signed_headers(method, request_path, body=""):
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")
    
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
        "Content-Type": "application/json",
        "x-simulated-trading": "0"  # Attiva la modalità di test simulato per verificare le chiavi
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
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "-1", "msg": str(e)}), 500

@app.route("/api/autopilot", methods=["POST"])
def toggle_autopilot():
    global autopilot_active
    data = request.get_json()
    autopilot_active = data.get("active", False)
    return jsonify({
        "status": "success", 
        "autopilot": autopilot_active
    })

@app.route("/api/trade", methods=["POST"])
def execute_trade():
    data = request.get_json()
    action = data.get("action", "BUY")
    symbol = data.get("symbol", "BTC-USDT")
    
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": symbol,
        "tdMode": "cash",
        "side": action.lower(),
        "ordType": "market",
        "sz": "0.0001"
    }
    
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    
    try:
        response = requests.post(BASE_URL + endpoint, headers=headers, data=body_str, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "-1", "msg": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
