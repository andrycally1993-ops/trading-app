import time
import base64
import hmac
import hashlib
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_KEY = "c3f9bfde-c611-4972-a293-79c5aa27cd88"
SECRET_KEY = "19091AD9B5B411792FEE66C79DF6B37BB"
PASSPHRASE = "King_939625"

BASE_URL = "https://my.okx.com"

def get_okx_time():
    """Sincronizza l'orario direttamente con i server di OKX per evitare errori 50102."""
    try:
        res = requests.get(BASE_URL + "/api/v5/public/time", timeout=3)
        data = res.json()
        if "data" in data and len(data["data"]) > 0:
            return str(data["data"][0]["ts"])
    except Exception:
        pass
    return str(int(time.time() * 1000))

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
    import json
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
    import json
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    url = BASE_URL + endpoint
    try:
        response = requests.post(url, headers=headers, data=body_str, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"code": "1", "msg": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
