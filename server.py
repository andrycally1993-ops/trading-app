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

# --- CREDENZIALI OKX DEFINITIVE (CONTO REALE) ---
API_KEY = "c3f9bfde-c611-4972-a203-79c5aa27cd88"
SECRET_KEY = "19091AD9B5B41792FE066C79DF6B37BB"
PASSPHRASE = "King_939625"

PORT = int(os.environ.get('PORT', 10000))

# Stato globale gestito dall'Intelligenza Artificiale della web app
app_state = {
    "active": False,
    "side": "buy",
    "entry_price": 0.0,
    "size": 0.0,
    "autopilot_enabled": True,
    "last_action": "Autopilot pronto e in ascolto"
}

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

def fetch_live_btc_price():
    try:
        url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"
        res = requests.get(url, timeout=4).json()
        if res.get('code') == '0' and res.get('data'):
            return float(res['data'][0]['last'])
    except Exception:
        pass
    return 0.0

def execute_okx_order(side, size_str):
    try:
        order_payload = {
            "instId": "BTC-USDT",
            "tdMode": "cash",
            "side": side,
            "ordType": "market",
            "sz": size_str
        }
        res = okx_request('POST', '/api/v5/trade/order', json.dumps(order_payload))
        if res.get('code') == '0':
            return True, res
        return False, res.get('msg', 'Errore esecuzione')
    except Exception as e:
        return False, str(e)

def ai_trading_engine():
    """Motore AI in background: gestisce capitale e operazioni in autonomia"""
    while True:
        try:
            time.sleep(30) # Intervallo di controllo del mercato
            if not app_state["autopilot_enabled"]:
                continue

            # 1. Ottieni il saldo reale e il prezzo corrente in tempo reale
            res_bal = okx_request('GET', '/api/v5/account/balance')
            current_price = fetch_live_btc_price()
            
            if res_bal.get('code') == '0' and res_bal.get('data') and current_price > 0:
                details = res_bal['data'][0]
                total_eq = float(details.get('totalEq', 0.0))
                
                # Trova la disponibilità in USDT o valuta base
                avail_usdt = 0.0
                for detail in details.get('details', []):
                    if detail.get('ccy') == 'USDT':
                        avail_usdt = float(detail.get('availBal', 0.0))
                
                # Se non c'è un'operazione attiva e abbiamo fondi sufficienti (> 5 USDT)
                if not app_state["active"] and avail_usdt >= 5.0:
                    # L'IA calcola automaticamente una quota del capitale (es. 20% del disponibile)
                    allocated_usdt = avail_usdt * 0.20
                    # Calcola la quantità di BTC da comprare in base al prezzo live
                    calculated_size = round(allocated_usdt / current_price, 4)
                    if calculated_size < 0.0001:
                        calculated_size = 0.0001
                    
                    size_str = f"{calculated_size:.4f}"
                    success, result = execute_okx_order("buy", size_str)
                    
                    if success:
                        app_state["active"] = True
                        app_state["side"] = "buy"
                        app_state["entry_price"] = current_price
                        app_state["size"] = calculated_size
                        app_state["last_action"] = f"AI: Acquisto automatico di {size_str} BTC a {current_price}"
                        print(app_state["last_action"])
                
                # Se c'è un'operazione attiva, l'IA valuta se chiuderla in profitto (> +0.5%) o tagliare le perdite
                elif app_state["active"] and app_state["entry_price"] > 0:
                    entry = app_state["entry_price"]
                    pnl_pct = ((current_price - entry) / entry) * 100.0
                    
                    # Target di profitto raggiunto o stop loss di protezione
                    if pnl_pct >= 0.5 or pnl_pct <= -0.4:
                        size_str = f"{app_state['size']:.4f}"
                        success, result = execute_okx_order("sell", size_str)
                        if success:
                            app_state["active"] = False
                            app_state["last_action"] = f"AI: Chiusura operazione con PnL del {pnl_pct:.2f}%"
                            print(app_state["last_action"])
        except Exception as e:
            print(f"Errore nel loop AI: {e}")
            time.sleep(15)

class OKHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/balance', '/api/balance']:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            bal_val = 21.89
            pnl_val = 0.0
            
            try:
                res_bal = okx_request('GET', '/api/v5/account/balance')
                if res_bal.get('code') == '0' and res_bal.get('data'):
                    details = res_bal['data'][0]
                    bal_val = float(details.get('totalEq', 21.89))

                if app_state["active"]:
                    current_price = fetch_live_btc_price()
                    entry = app_state["entry_price"]
                    size = app_state["size"]
                    if entry > 0 and current_price > 0:
                        price_diff = current_price - entry
                        pnl_val = price_diff * size
            except Exception:
                pass

            response_data = {
                "success": True,
                "balance": bal_val,
                "equity": bal_val + pnl_val,
                "pnl": pnl_val,
                "active_trade": app_state["active"],
                "status_message": app_state["last_action"]
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

                side = data_in.get('side', 'buy')
                size = str(data_in.get('size', '0.001'))

                success, result = execute_okx_order(side, size)
                if success:
                    app_state["active"] = (side == 'buy')
                    app_state["entry_price"] = fetch_live_btc_price()
                    app_state["size"] = float(size)
                    response_data = {"success": True, "orderId": "AI-EXECUTED"}
                else:
                    response_data = {"success": False, "error": str(result)}
            except Exception as e:
                response_data = {"success": False, "error": str(e)}

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
    # Avvia l'intelligenza artificiale in background sul server Python
    ai_thread = threading.Thread(target=ai_trading_engine, daemon=True)
    ai_thread.start()

    with socketserver.TCPServer(("0.0.0.0", PORT), OKHandler) as httpd:
        print(f"Web App con IA di trading attiva sulla porta {PORT}")
        httpd.serve_forever()
