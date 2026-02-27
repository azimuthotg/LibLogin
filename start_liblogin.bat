@echo off
REM =====================================================
REM LibLogin Service Startup Script
REM สำหรับใช้กับ NSSM Windows Service
REM =====================================================

REM เปลี่ยนไปยังโฟลเดอร์โปรเจกต์
cd /d C:\inetpub\LibLogin

REM เปิดใช้งาน Virtual Environment
call venv\Scripts\activate.bat

REM รัน Waitress Server
python run_server.py
