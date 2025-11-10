@echo off
REM =====================================================
REM LibLogin Backup Script
REM ทำการ backup database และ media files
REM =====================================================

REM สร้าง timestamp
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM ไปยังโฟลเดอร์โปรเจกต์
cd /d C:\inetpub\LibLogin

REM สร้างโฟลเดอร์ backups ถ้ายังไม่มี
if not exist "backups" mkdir backups
if not exist "backups\media" mkdir backups\media

REM Backup database
echo.
echo =====================================================
echo Backing up database...
echo =====================================================
copy db.sqlite3 "backups\db_%TIMESTAMP%.sqlite3"
if %errorlevel% equ 0 (
    echo [SUCCESS] Database backup: db_%TIMESTAMP%.sqlite3
) else (
    echo [ERROR] Database backup failed!
)

REM Backup media files
echo.
echo =====================================================
echo Backing up media files...
echo =====================================================
xcopy media "backups\media_%TIMESTAMP%\" /E /I /Y /Q
if %errorlevel% equ 0 (
    echo [SUCCESS] Media backup: media_%TIMESTAMP%\
) else (
    echo [ERROR] Media backup failed!
)

REM ลบ backup เก่าที่เกิน 30 วัน (optional)
echo.
echo =====================================================
echo Cleaning old backups (older than 30 days)...
echo =====================================================
forfiles /p "backups" /s /m *.sqlite3 /d -30 /c "cmd /c del @path" 2>nul
forfiles /p "backups" /s /m media_* /d -30 /c "cmd /c rd /s /q @path" 2>nul

echo.
echo =====================================================
echo Backup completed at %date% %time%
echo =====================================================
echo.

REM เก็บ log
echo %date% %time% - Backup completed >> backups\backup.log
