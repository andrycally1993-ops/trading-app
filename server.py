import os
import time
import hmac
import base64
import hashlib
from datetime import datetime
import requests
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Caricamento sicuro delle credenziali dalle variabili d'ambiente di Render
API_KEY = os.getenv("API_KEY", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
PASSPHRASE = os.getenv("PASSPHRASE", "").strip()

# Endpoint ufficiale di produzione OKX (Conto Reale)
BASE_URL = "https://www.okx.com"

def get_signed_headers(method, request_path, body=""):
    """Genera la firma crittografica HMAC-SHA256 richiesta da OKX V5"""
    timestamp = datetime.utcnow().isoformat() + "Z"
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
    # Restituisce la pagina principale dell'app (assicurati che il file HTML sia nella cartella templates)
    return render_template("index.html")

@app.route("/api/balance", methods=["GET"])
def check_balance():
    """Rotta di test per verificare la connessione e la lettura del saldo su OKX"""
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

# Aggiungi qui sotto le tue eventuali altre rotte per gli ordini (POST /api/trade, ecc.)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
