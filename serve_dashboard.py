#!/usr/bin/env python3
"""
Simple HTTP server to view the dashboard
"""

import http.server
import socketserver
import webbrowser
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def serve_dashboard():
    """Start HTTP server and open dashboard in browser"""

    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print(f"🚀 Dashboard server running at {url}")
        print(f"📊 Opening dashboard in your browser...")
        print(f"\n   Press Ctrl+C to stop the server\n")

        # Open browser
        webbrowser.open(url)

        # Serve forever
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard server stopped")

if __name__ == "__main__":
    serve_dashboard()
