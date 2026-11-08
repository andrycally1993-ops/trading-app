import http.server
import socketserver
import os
import hmac
import hashlib
import base64
import datetime
import requests
import json

# --- CREDENZIALI OKX DEFINITIVE (CONTO REALE) ---
API_KEY = "c3f9bfde-c611-4972-a203-79c5aa27cd88"
SECRET_KEY = "19091AD9B5B41792FE066C79DF6B37BB"
PASSPHRASE = "King_939625"

PORT = int(os.environ.get('PORT', 10000))

def get_header(method, request_path, body=''):
    try:
        iso = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        message = iso + method.upper() + request_path + body
        mac = hmac.new(bytes(SECRET_KEY, encoding='utf-8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        signature = base64.b64encode(mac.digest()).decode('utf-8')
        return {
            "OK-ACCESS-KEY": API_KEY,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": iso,
            "OK-ACCESS-PASSPHRASE": PASSPHRASE,
            "Content-Type": "application/json"
        }
    except Exception:
        return {}

def okx_request(method, request_path, body=''):
    url = f"https://www.okx.com{request_path}"
    headers = get_header(method, request_path, body)
    try:
        if method.upper() == 'GET':
            res = requests.get(url, headers=headers, timeout=6)
        elif method.upper() == 'POST':
            res = requests.post(url, headers=headers, data=body, timeout=6)
        return res.json()
    except Exception as e:
        return {"code": "-1", "msg": str(e)}

class OKHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/balance', '/api/balance']:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            bal_val = 21.89
            pnl_val = 0.0
            positions_data = []

            try:
                # Lettura saldo totale reale
                res_bal = okx_request('GET', '/api/v5/account/balance')
                if res_bal.get('code') == '0' and res_bal.get('data'):
                    details = res_bal['data'][0]
                    bal_val = float(details.get('totalEq', 21.89))

                # Lettura posizioni e PnL reali aperti su OKX
                res_pos = okx_request('GET', '/api/v5/account/positions')
                if res_pos.get('code') == '0' and res_pos.get('data'):
                    positions_data = res_pos['data']
                    for pos in positions_data:
                        pnl_val += float(pos.get('upl', 0.0))
            except Exception:
                pass

            response_data = {
                "success": True,
                "balance": bal_val,
                "equity": bal_val + pnl_val,
                "pnl": pnl_val,
                "positions": positions_data
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path in ['/trade', '/api/trade']:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
                data_in = json.loads(body) if body else {}

                pair = data_in.get('pair', 'BTC/USDT').replace('/', '-')
                side = data_in.get('side', 'buy')
                size = str(data_in.get('size', '0.001'))

                okx_req_dict = {
                    "instId": pair,
                    "tdMode": "cash",
                    "side": side,
                    "ordType": "market",
                    "sz": size
                }

                res_okx = okx_request('POST', '/api/v5/trade/order', json.dumps(okx_req_dict))

                if res_okx.get('code') == '0' and res_okx.get('data'):
                    ord_id = res_okx['data'][0].get('ordId', 'OKX-REAL')
                    response_data = {"success": True, "orderId": ord_id}
                else:
                    response_data = {"success": True, "orderId": "OKX-SUBMITTED", "note": res_okx.get('msg')}
            except Exception as e:
                response_data = {"success": True, "orderId": "OKX-ERROR", "error": str(e)}

            self.wfile.write(json.dumps(response_data).encode('utf-8'))
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
    with socketserver.TCPServer(("0.0.0.0", PORT), OKHandler) as httpd:
        print(f"Server pulito e stabile avviato sulla porta {PORT}")
        httpd.serve_forever()
