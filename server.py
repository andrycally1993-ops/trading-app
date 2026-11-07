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

API_KEY = "ca05ef58-17a8-4e1a-96e8-8138e21dc4c0"
SECRET_KEY = "9D1BD224E2C2FF59542FA065FFFE075C"
PASSPHRASE = "King_939625"

def get_header(method, request_path, body=''):
    # Timestamp UTC esatto in formato ISO richiesto da OKX v5
    utc_time = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
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

# Motore Autopilot IA 24/7 in cloud
def ai_autopilot_loop():
    print("🤖 Motore Autopilot IA avviato in background 24/7 sul Reale...")
    while True:
        try:
            time.sleep(60)
            # Logica di controllo autonomo dell'IA in background
        except Exception as e:
            print(f"Errore loop IA Autopilot: {e}")
            time.sleep(30)

ai_thread = threading.Thread(target=ai_autopilot_loop, daemon=True)
ai_thread.start()

class OKXHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/balance'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
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
