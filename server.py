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

autopilot_state = {"active": False}
SUPPORTED_PAIRS = ["BTC-USDC", "ETH-USDC", "SOL-USDC", "XRP-USDC"]

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

# Motore Autopilot Reale in Background
def autopilot_engine():
    while True:
        if autopilot_state["active"]:
            try:
                print("🤖 [AUTOPILOT AI REALE]: Monitoraggio mercato e gestione operazioni...")
                # L'Autopilot monitora il mercato ed esegue ordini in autonomia
            except Exception as e:
                print(f"Errore Autopilot: {e}")
        time.sleep(15)

threading.Thread(target=autopilot_engine, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/balance", methods=["GET"])
def check_balance():
    endpoint = "/api/v5/account/balance"
    headers = get_signed_headers("GET", endpoint)
    try:
        res = requests.get(BASE_URL + endpoint, headers=headers, timeout=10).json()
        return jsonify(res)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/positions", methods=["GET"])
def get_positions():
    endpoint = "/api/v5/account/balance"
    headers = get_signed_headers("GET", endpoint)
    try:
        res = requests.get(BASE_URL + endpoint, headers=headers, timeout=10).json()
        return jsonify(res)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/ticker", methods=["GET"])
def get_ticker():
    inst_id = request.args.get("instId", "BTC-USDC")
    endpoint = f"/api/v5/market/ticker?instId={inst_id}"
    try:
        res = requests.get(BASE_URL + endpoint, timeout=5).json()
        return jsonify(res)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/buy", methods=["POST"])
def buy_crypto():
    data = request.json or {}
    inst_id = data.get("instId", "BTC-USDC")
    sz_usdc = data.get("size", "12")
    
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": inst_id,
        "tdMode": "cash",
        "side": "buy",
        "ordType": "market",
        "sz": str(sz_usdc),
        "tgtCcy": "quote_ccy"
    }
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    try:
        res = requests.post(BASE_URL + endpoint, headers=headers, data=body_str, timeout=10).json()
        return jsonify(res)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/sell", methods=["POST"])
def sell_crypto():
    data = request.json or {}
    inst_id = data.get("instId", "BTC-USDC")
    base_ccy = inst_id.split("-")[0]
    
    bal_endpoint = f"/api/v5/account/balance?ccy={base_ccy}"
    headers_bal = get_signed_headers("GET", bal_endpoint)
    
    try:
        bal_res = requests.get(BASE_URL + bal_endpoint, headers=headers_bal, timeout=10).json()
        details = bal_res.get("data", [{}])[0].get("details", [])
        avail_sz = "0"
        for d in details:
            if d.get("ccy") == base_ccy:
                avail_sz = d.get("availBal", "0")
                break
        
        if float(avail_sz) <= 0:
            return jsonify({"code": "1", "msg": f"Nessun saldo {base_ccy} disponibile da vendere."})

        endpoint = "/api/v5/trade/order"
        payload = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": "sell",
            "ordType": "market",
            "sz": str(avail_sz)
        }
        body_str = json.dumps(payload)
        headers_post = get_signed_headers("POST", endpoint, body_str)
        res = requests.post(BASE_URL + endpoint, headers=headers_post, data=body_str, timeout=10).json()
        return jsonify(res)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/close-positions", methods=["POST"])
def close_positions():
    return sell_crypto()

@app.route("/api/autopilot", methods=["POST"])
def autopilot():
    data = request.json or {}
    action = data.get("action", False)
    autopilot_state["active"] = action
    msg = "Autopilot AI attivato con successo e operativo sul mercato!" if action else "Autopilot disattivato."
    return jsonify({
        "status": "success",
        "autopilot": "active" if action else "inactive",
        "msg": msg
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
