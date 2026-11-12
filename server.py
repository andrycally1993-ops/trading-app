import time
import datetime
import base64
import hmac
import hashlib
import json
import threading
import random
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_KEY = "e059ce24-96a8-445d-b374-bfad44938d9c"
SECRET_KEY = "1BFCDA6FEF287CAC00B8D96FD222EF4A"
PASSPHRASE = "King_939625"

BASE_URL = "https://my.okx.com"

autopilot_state = {"active": False}
autopilot_logs = []
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

def execute_okx_buy(inst_id, size_usdc):
    endpoint = "/api/v5/trade/order"
    payload = {
        "instId": inst_id,
        "tdMode": "cash",
        "side": "buy",
        "ordType": "market",
        "sz": str(size_usdc),
        "tgtCcy": "quote_ccy"
    }
    body_str = json.dumps(payload)
    headers = get_signed_headers("POST", endpoint, body_str)
    try:
        res = requests.post(BASE_URL + endpoint, headers=headers, data=body_str, timeout=10).json()
        return res
    except Exception as e:
        return {"code": "1", "msg": str(e)}

# Motore Autopilot IA Reale
def autopilot_ai_worker():
    while True:
        if autopilot_state["active"]:
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            try:
                log_msg = f"[{timestamp}] 🤖 Autopilot AI: Analisi mercati in corso..."
                autopilot_logs.insert(0, log_msg)
                
                bal_endpoint = "/api/v5/account/balance"
                headers_bal = get_signed_headers("GET", bal_endpoint)
                bal_res = requests.get(BASE_URL + bal_endpoint, headers=headers_bal, timeout=10).json()
                
                details = bal_res.get("data", [{}])[0].get("details", [])
                usdc_avail = 0.0
                for d in details:
                    if d.get("ccy") == "USDC":
                        usdc_avail = float(d.get("availBal", 0))
                
                # Controlla se ci sono già posizioni crypto aperte
                allowed_crypto = ['BTC', 'ETH', 'SOL', 'XRP']
                has_open_position = any(d.get("ccy") in allowed_crypto and float(d.get("availBal", 0)) > 0.0001 for d in details)

                if not has_open_position and usdc_avail >= 12.0:
                    chosen_pair = random.choice(SUPPORTED_PAIRS)
                    buy_res = execute_okx_buy(chosen_pair, "12")
                    if buy_res.get("code") == "0":
                        success_msg = f"[{timestamp}] ✅ Autopilot IA ha acquistato 12 USDC su {chosen_pair}!"
                        autopilot_logs.insert(0, success_msg)
                    else:
                        err_msg = f"[{timestamp}] ❌ Autopilot errore su {chosen_pair}: {buy_res.get('msg')}"
                        autopilot_logs.insert(0, err_msg)
                else:
                    info_msg = f"[{timestamp}] ℹ️ Autopilot in attesa (Posizione aperta esistente o saldo USDC {usdc_avail} insufficiente)."
                    autopilot_logs.insert(0, info_msg)
            except Exception as e:
                err_sys = f"[{timestamp}] ❌ Autopilot eccezione: {str(e)}"
                autopilot_logs.insert(0, err_sys)
        time.sleep(40)

threading.Thread(target=autopilot_ai_worker, daemon=True).start()

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

@app.route("/api/autopilot-logs", methods=["GET"])
def get_autopilot_logs():
    return jsonify({"active": autopilot_state["active"], "logs": autopilot_logs[:15]})

@app.route("/api/buy", methods=["POST"])
def buy_crypto():
    data = request.json or {}
    inst_id = data.get("instId", "BTC-USDC")
    sz_usdc = data.get("size", "12")
    res = execute_okx_buy(inst_id, sz_usdc)
    return jsonify(res)

@app.route("/api/sell", methods=["POST"])
def sell_crypto():
    bal_endpoint = "/api/v5/account/balance"
    headers_bal = get_signed_headers("GET", bal_endpoint)
    try:
        bal_res = requests.get(BASE_URL + bal_endpoint, headers=headers_bal, timeout=10).json()
        details = bal_res.get("data", [{}])[0].get("details", [])
        
        allowed_crypto = ['BTC', 'ETH', 'SOL', 'XRP']
        target_ccy = None
        avail_sz = "0"
        
        for d in details:
            if d.get("ccy") in allowed_crypto and float(d.get("availBal", 0)) > 0.00001:
                target_ccy = d.get("ccy")
                avail_sz = d.get("availBal")
                break
        
        if not target_ccy or float(avail_sz) <= 0:
            return jsonify({"code": "1", "msg": "Nessuna posizione crypto attiva da vendere."})

        inst_id = f"{target_ccy}-USDC"
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
