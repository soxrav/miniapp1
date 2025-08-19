import http.server
import socketserver
import webbrowser

PORT = 8000


class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
    print(f"🚀 Сервер запущен на http://localhost:{PORT}")
    print("📱 Откройте браузер или используйте в Telegram")
    webbrowser.open(f'http://localhost:{PORT}')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")