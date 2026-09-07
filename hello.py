from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime


class DevOpsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        timestamp = datetime.now().isoformat()

        print(f"{timestamp} - GET request received for {self.path}", flush=True)

        if self.path == "/health":
            response = "healthy"
            status_code = 200
        elif self.path == "/":
            response = "Hello, DevOps!"
            status_code = 200
        else:
            response = "Not Found"
            status_code = 404

        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(response.encode())))
        self.end_headers()
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        print(f"{datetime.now().isoformat()} - {format % args}", flush=True)


if __name__ == "__main__":
    server_address = ("0.0.0.0", 8080)
    server = HTTPServer(server_address, DevOpsHandler)

    print("DevOps application running on port 8080", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped", flush=True)
    finally:
        server.server_close()