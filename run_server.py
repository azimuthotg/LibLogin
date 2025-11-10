"""
LibLogin Waitress Server Runner
สำหรับรันบน Windows Server ด้วย Waitress WSGI Server
"""

from waitress import serve
from backend.wsgi import application
import os
import sys

if __name__ == '__main__':
    # ตั้งค่า environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

    # กำหนด host และ port
    HOST = '0.0.0.0'
    PORT = 8000

    print("=" * 60)
    print("LibLogin - Library WiFi Login Management System")
    print("=" * 60)
    print(f"Starting Waitress WSGI Server...")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"URL: http://localhost:{PORT}")
    print("-" * 60)
    print("Press Ctrl+C to quit")
    print("=" * 60)

    try:
        # รัน Waitress
        serve(
            application,
            host=HOST,
            port=PORT,
            threads=4,              # จำนวน threads (ปรับตาม CPU cores)
            channel_timeout=60,     # Timeout 60 วินาที
            cleanup_interval=10,    # Cleanup interval
            url_scheme='http'
        )
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server stopped by user")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {str(e)}")
        print("=" * 60)
        sys.exit(1)
