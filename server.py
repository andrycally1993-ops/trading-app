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

def autopilot_worker():
    while True:
        if autopilot_state["active"]:
            try:
                print("🤖 Autopilot attivo: monitoraggio BTC-USDC...")
            except Exception as e:
                print(f"Errore Autopilot: {e}")
        time.sleep(15)

threading.Thread(target=autopilot_worker, daemon=True).start()

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
        assets = []
        if res.get("code") == "0" and res.get("data"):
            details = res["data"][0].get("details", [])
            for item in details:
                avail = float(item.get("availBal", 0))
                if avail > 0:
                    assets.append({
                        "ccy": item.get("ccy"),
                        "balance": item.get("availBal"),
                        "eq": item.get("eq")
                    })
        return jsonify({"code": "0", "assets": assets})
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/buy", methods=["POST"])
def buy_crypto():
    size = request.json.get("size", "0.0002")
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": "BTC-USDC",
        "tdMode": "cash",
        "side": "buy",
        "ordType": "market",
        "sz": size
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
    size = request.json.get("size", "0.0002")
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": "BTC-USDC",
        "tdMode": "cash",
        "side": "sell",
        "ordType": "market",
        "sz": size
    }
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    try:
        res = requests.post(BASE_URL + endpoint, headers=headers, data=body_str, timeout=10).json()
        return jsonify(res)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/close-positions", methods=["POST"])
def close_positions():
    endpoint_bal = "/api/v5/account/balance?ccy=BTC"
    headers_bal = get_signed_headers("GET", endpoint_bal)
    try:
        res_bal = requests.get(BASE_URL + endpoint_bal, headers=headers_bal, timeout=10).json()
        btc_bal = "0"
        if res_bal.get("code") == "0" and res_bal.get("data"):
            details = res_bal["data"][0].get("details", [])
            if details:
                btc_bal = details[0].get("availBal", "0")
        
        if float(btc_bal) <= 0:
            return jsonify({"code": "0", "msg": "Nessun BTC da vendere/chiudere."})
            
        endpoint_order = "/api/v5/trade/order"
        payload = {
            "instId": "BTC-USDC",
            "tdMode": "cash",
            "side": "sell",
            "ordType": "market",
            "sz": btc_bal
        }
        body_str = json.dumps(payload)
        headers_order = get_signed_headers("POST", endpoint_order, body_str)
        res_sell = requests.post(BASE_URL + endpoint_order, headers=headers_order, data=body_str, timeout=10).json()
        return jsonify(res_sell)
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

@app.route("/api/autopilot", methods=["POST"])
def autopilot():
    action = request.json.get("action", False)
    autopilot_state["active"] = action
    return jsonify({
        "status": "success",
        "autopilot": "active" if action else "inactive",
        "msg": "Autopilot " + ("ATTIVATO" if action else "DISATTIVATO")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
