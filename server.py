import http.server
import socketserver
import hmac
import hashlib
import base64
import datetime
import requests
import json
import threading
import time

PORT = 8000

# Credenziali predefinite
API_KEY = "f2f94d98-56b4-4c5a-b363-980a24b16839"
SECRET_KEY = "F4BC6222EC9594F4DB889A1B5532"
PASSPHRASE = "King_9396"

class OKXHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        global API_KEY, SECRET_KEY, PASSPHRASE
        if self.path == '/api/config':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                if data.get('apiKey'): API_KEY = data.get('apiKey').strip()
                if data.get('secretKey'): SECRET_KEY = data.get('secretKey').strip()
                if data.get('passphrase'): PASSPHRASE = data.get('passphrase').strip()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "updated"}).encode('utf-8'))
                return
            except Exception as e:
                print("Errore aggiornamento API:", e)

        self.send_response(400)
        self.end_headers()

    def do_GET(self):
        global API_KEY, SECRET_KEY, PASSPHRASE
        if self.path == '/api/balance':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

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

                if res_data.get('code') == '0' and len(res_data.get('data', [])) > 0:
                    balance_info = res_data['data'][0]
                    actual_bal = balance_info.get('totalEq', '0.00')
                    
                    usdc_avail = "0.00"
                    for detail in balance_info.get('details', []):
                        if detail.get('ccy') == 'USDC':
                            usdc_avail = detail.get('availEq', detail.get('cashBal', '0.00'))
                            break

                    final_bal = usdc_avail if float(usdc_avail) > 0 else actual_bal
                    payload = {
                        "balance": final_bal,
                        "equity": actual_bal,
                        "real": True
                    }
                    self.wfile.write(json.dumps(payload).encode('utf-8'))
                    return
            except Exception as e:
                print("Errore chiamata OKX:", e)

            # Fallback se le API OKX sono momentaneamente irraggiungibili o vuote
            fallback = {
                "balance": "0.00",
                "equity": "0.00",
                "real": True
            }
            self.wfile.write(json.dumps(fallback).encode('utf-8'))
            return

        super().do_GET()

def cloud_ai_autopilot_worker():
    while True:
        time.sleep(15)

if __name__ == '__main__':
    ai_thread = threading.Thread(target=cloud_ai_autopilot_worker, daemon=True)
    ai_thread.start()

    with socketserver.TCPServer(("", PORT), OKXHandler) as httpd:
        httpd.serve_forever()
