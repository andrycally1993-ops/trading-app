import http.server
import socketserver
import hmac
import hashlib
import base64
import datetime
import requests
import json

PORT = 8000

# ==========================================================
# INSERISCI QUI LE TUE CHIAVI REALI DI OKX TRA LE VIRGOLETTE:
# ==========================================================
API_KEY = "f2f94d98-56b4-4c5a-b363-980a2b416839"
SECRET_KEY = "F4C8CC6222EC9594F9D4BBB89A1B5532"
PASSPHRASE = "King_9396"
USE_REAL = True  # True = Conto Reale, False = Demo
# ==========================================================

class OKXHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        global API_KEY, SECRET_KEY, PASSPHRASE, USE_REAL
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/api/config':
                # Se vuoi puoi anche aggiornarle dal sito, ma userà quelle sopra se lasciate vuote
                incoming_key = data.get('apiKey', '').strip()
                if incoming_key:
                    API_KEY = incoming_key
                    SECRET_KEY = data.get('secretKey', '').strip()
                    PASSPHRASE = data.get('passphrase', '').strip()
                    USE_REAL = data.get('env', 'demo') == 'real'
                
                print(f"--> CONFIG AGGIORNATA! Reale: {USE_REAL} | API Key: {API_KEY[:6]}...")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "real": USE_REAL}).encode('utf-8'))
                return
        except Exception as e:
            print("Errore nel POST:", e)
        
        self.send_response(400)
        self.end_headers()

    def do_GET(self):
        global API_KEY, SECRET_KEY, PASSPHRASE, USE_REAL
        if self.path == '/api/balance':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Controlliamo se ci sono chiavi valide inserite
            has_valid_keys = bool(API_KEY and API_KEY != "INSERISCI_QUI_LA_TUA_API_KEY" and SECRET_KEY and PASSPHRASE)
            
            if USE_REAL and has_valid_keys:
                try:
                    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    path = '/api/v5/account/balance'
                    method = 'GET'
                    
                    message = timestamp + method + path
                    signature = base64.b64encode(
                        hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
                    ).decode('utf-8')
                    
                    headers = {
                        'OK-ACCESS-KEY': API_KEY,
                        'OK-ACCESS-SIGN': signature,
                        'OK-ACCESS-TIMESTAMP': timestamp,
                        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
                        'Content-Type': 'application/json'
                    }
                    
                    url = 'https://www.okx.com' + path
                    response = requests.get(url, headers=headers, timeout=5)
                    res_data = response.json()
                    
                    print("Risposta OKX Balance:", res_data)
                    
                    if res_data.get('code') == '0' and len(res_data.get('data', [])) > 0:
                        total_eq = float(res_data['data'][0].get('totalEq', 0))
                        balance_info = {
                            "balance": total_eq,
                            "equity": total_eq,
                            "real": True
                        }
                        self.wfile.write(json.dumps(balance_info).encode('utf-8'))
                        return
                except Exception as e:
                    print("Errore di connessione alle API OKX:", e)
            
            # Se siamo in reale senza chiavi o se la chiamata fallisce, mostra 0.00
            current_balance = 0.00 if USE_REAL else 10000.00
            fallback_info = {
                "balance": current_balance,
                "equity": current_balance,
                "real": USE_REAL
            }
            self.wfile.write(json.dumps(fallback_info).encode('utf-8'))
        else:
            super().do_GET()

print(f"Server Python avviato sulla porta {PORT} con credenziali integrate...")
with socketserver.TCPServer(("", PORT), OKXHandler) as httpd:
    httpd.serve_forever()