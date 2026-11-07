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
import urllib.parse

# Lettura della porta assegnata da Render (o 8000 di default)
PORT = int(os.environ.get('PORT', 8000))

# Lettura delle credenziali dalle variabili d'ambiente
API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
PASSPHRASE = os.environ.get('PASSPHRASE')

# Funzione per firmare le richieste API per OKX (Live Trading)
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
        'OK-ACCESS-FLAG': '0',  # '0' indica l'account Live/Reale, '1' per la demo
        'Content-Type': 'application/json'
    }
    return header

class OKXHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/balance':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                request_path = '/api/v5/account/balance'
                url = 'https://www.okx.com' + request_path
                headers = get_header('GET', request_path)
                
                response = requests.get(url, headers=headers)
                self.wfile.write(response.content)
            except Exception as e:
                error_response = json.dumps({"error": str(e)})
                self.wfile.write(error_response.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/trade':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                # Legge i dati dell'ordine inviati dalla web app
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
                
                request_path = '/api/v5/trade/order'
                url = 'https://www.okx.com' + request_path
                headers = get_header('POST', request_path, body)
                
                response = requests.post(url, headers=headers, data=body)
                self.wfile.write(response.content)
            except Exception as e:
                error_response = json.dumps({"error": str(e)})
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
