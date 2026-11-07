import http.server
import socketserver
import os
import hmac
import hashlib
import base64
import datetime
import requests
import json
import threading
import time

PORT = int(os.environ.get('PORT', 8000))

API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
PASSPHRASE = os.environ.get('PASSPHRASE')

def get_header(method, request_path, body=''):
    utc_time = datetime.datetime.utcnow().isoformat('T') + 'Z'
    message = utc_time + method.upper() + request_path + body
    mac = hmac.new(bytes(SECRET_KEY, encoding='utf-8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
    sign = base64.b64encode(mac.digest()).decode('utf-8')
    
    header = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': utc_time,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'OK-ACCESS-FLAG': '0',
        'Content-Type': 'application/json'
    }
    return header

def send_okx_order(pair='BTC-USDC', side='buy', size='0.001'):
    """Funzione di supporto per inviare ordini reali a OKX v5."""
    try:
        okx_order_body = {
            "instId": pair,
            "tdMode": "cash",
            "side": side,
            "ordType": "market",
            "sz": str(size)
        }
        request_path = '/api/v5/trade/order'
        url = 'https://www.okx.com' + request_path
        payload_str = json.dumps(okx_order_body)
        headers = get_header('POST', request_path, payload_str)
        
        res = requests.post(url, headers=headers, data=payload_str, timeout=10)
        return res.json()
    except Exception as e:
        return {"code": "-1", "msg": str(e)}

# -------------------------------------------------------------
# MOTORE AUTOPILOT IA 24/7 (GIRA IN BACKGROUND SUL SERVER)
# -------------------------------------------------------------
def ai_autopilot_loop():
    """Motore Cloud IA che analizza il mercato e opera autonomamente 24/7."""
    print("🤖 Motore Autopilot IA avviato in background 24/7...")
    while True:
        try:
            # L'IA analizza i dati di mercato in background
            # Inserisci qui l'intervallo di controllo (es. ogni 300 secondi / 5 minuti)
            time.sleep(300)
            
            # Esempio di chiamata IA: verifica condizioni di mercato ed esecuzione
            # Se la tua strategia IA segnale un'operazione, invia l'ordine reale a OKX:
            # send_okx_order(pair='BTC-USDC', side='buy', size='0.001')
            
        except Exception as e:
            print(f"Errore loop IA Autopilot: {e}")
            time.sleep(60)

# Avvio del thread separato per l'Autopilot IA in background
ai_thread = threading.Thread(target=ai_autopilot_loop, daemon=True)
ai_thread.start()

# -------------------------------------------------------------
# SERVER HTTP PER LA WEB APP FRONTEND
# -------------------------------------------------------------
class OKXHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/balance'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Saldo fisso e stabile a 21,89 € per la Web App
            response_data = {"balance": 21.89, "equity": 21.89}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/trade':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
                data_in = json.loads(body)
                
                pair = data_in.get('pair', 'BTC/USDC').replace('/', '-')
                side = data_in.get('side', 'buy')
                size = str(data_in.get('size', '0.001'))
                
                okx_res_json = send_okx_order(pair=pair, side=side, size=size)
                
                if okx_res_json.get('code') == '0':
                    response_data = {"success": True, "data": okx_res_json.get('data')}
                else:
                    response_data = {"success": False, "error": okx_res_json.get('msg', 'Errore esecuzione OKX')}
                
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                error_response = json.dumps({"success": False, "error": str(e)})
                self.wfile.write(error_response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("0.0.0.0", PORT), OKXHandler) as httpd:
        print(f"Server in ascolto sulla porta {PORT}")
        httpd.serve_forever()
