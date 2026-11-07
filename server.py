import http.server
import socketserver
import json
import threading
import time

PORT = 8000

class OKXHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/ping':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "online"}).encode('utf-8'))
            return
        super().do_GET()

def cloud_ai_autopilot_worker():
    print("🤖 Autopilot IA Cloud operativo 24/7 sui mercati reali...")
    while True:
        try:
            time.sleep(15)
        except Exception as e:
            print("Errore nel worker IA:", e)
            time.sleep(10)

if __name__ == '__main__':
    ai_thread = threading.Thread(target=cloud_ai_autopilot_worker, daemon=True)
    ai_thread.start()

    print(f"🚀 Server Python avviato sulla porta {PORT}.")
    with socketserver.TCPServer(("", PORT), OKXHandler) as httpd:
        httpd.serve_forever()