import os
import time
import hmac
import base64
import hashlib
import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Caricamento sicuro delle credenziali dalle variabili d'ambiente di Render
API_KEY = os.getenv("API_KEY", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
PASSPHRASE = os.getenv("PASSPHRASE", "").strip()

# Endpoint ufficiale di produzione OKX (Conto Reale)
BASE_URL = "https://www.okx.com"

def get_okx_server_time_diff():
    """Calcola lo scarto di tempo tra il server Render e i server ufficiali OKX"""
    try:
        response = requests.get(f"{BASE_URL}/api/v5/public/time", timeout=5)
        if response.status_code == 200:
            data = response.json()
            server_time_ms = int(data['data'][0]['ts'])
            local_time_ms = int(time.time() * 1000)
            return server_time_ms - local_time_ms
    except Exception as e:
        print(f"Errore sincronizzazione orario OKX: {e}")
    return 0  # Fallback a zero se la chiamata fallisce

def get_signed_headers(method, request_path, body=""):
    """Genera la firma crittografica HMAC-SHA256 con timestamp sincronizzato con OKX"""
    # Sincronizza il timestamp al millisecondo esatto usando l'orario ufficiale OKX
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
    # Restituisce la pagina principale dalla cartella templates
    return render_template("index.html")

@app.route("/api/balance", methods=["GET"])
def check_balance():
    """Rotta per verificare la connessione e leggere il saldo reale su OKX"""
    endpoint = "/api/v5/account/balance"
    headers = get_signed_headers("GET", endpoint)
    url = BASE_URL + endpoint
    
    print(f"--- Tentativo di connessione a OKX con API Key: {API_KEY[:6]}... ---")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code OKX: {response.status_code}")
        print(f"Risposta Grezza OKX: {response.text}")
        
        data = response.json()
        return jsonify(data)
    except Exception as e:
        print(f"Errore di connessione a OKX: {str(e)}")
        return jsonify({"code": "-1", "msg": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
