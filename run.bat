@echo off
setlocal ENABLEEXTENSIONS
chcp 65001 >nul
cd /d "%~dp0"

call :run docker compose version || goto :fail
call :run docker compose up -d --build || goto :fail

echo.
echo [LOGS] tailing bot logs (Ctrl+C to stop)...
call :run docker compose logs -f bot
goto :end

:run
echo.
echo ^> %*
%*
exit /b %ERRORLEVEL%

:fail
echo.
echo *** FAILED. See message above. ***
pause
:end
endlocal