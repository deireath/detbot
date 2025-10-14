@echo off
setlocal
chcp 65001 >nul
REM перейти в папку скрипта (важно при двойном клике)
cd /d "%~dp0"

echo [RUN] docker compose up -d --build
docker compose up -d --build

echo.
echo [LOGS] tailing bot logs (Ctrl+C to stop viewing logs; бот продолжит работать)...
docker compose logs -f bot

echo.
echo [DONE] Logs stream stopped. Containers are still running.
pause
endlocal