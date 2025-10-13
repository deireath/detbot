@echo off
call venv\Scripts\activate

python -m migrations.create_tables
python -m main
pause