@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo [DOWN] stopping containers...
docker compose down

pause
endlocal