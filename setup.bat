@echo off

docker compose up -d

echo Ждем готовности Postgres...
:wait_postgres
docker exec -i postgres pg_isready -U %POSTGRES_USER% -d %POSTGRES_DB% >nul 2>&1
IF ERRORLEVEL 1 (
    timeout /t 2 >nul
    goto wait_postgres
)
echo Postgres готов!


echo Ждем готовности Redis...
:wait_redis
docker exec -i redis redis-cli -a %REDIS_PASSWORD% PING | find "PONG" >nul
IF ERRORLEVEL 1 (
    timeout /t 2 >nul
    goto wait_redis
)
echo Redis готов!


call venv\Scripts\activate
python -m migrations.create_tables
python main.py
pause
