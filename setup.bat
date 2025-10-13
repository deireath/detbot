@echo off

python -m venv venv
сall venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Виртуально окружение готово...
pause