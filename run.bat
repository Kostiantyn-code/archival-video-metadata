@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
pushd "%~dp0"
if errorlevel 1 exit /b 1

if exist ".venv\Scripts\python.exe" goto check_env

py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto create_py
python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if not errorlevel 1 goto create_python
echo Не знайдено Python 3.10 або новішої версії.
echo Установіть 64-бітний Python з https://www.python.org/downloads/windows/
echo Під час встановлення увімкніть Add python.exe to PATH і повторіть запуск.
goto failed

:create_py
py -3 -m venv .venv
if errorlevel 1 goto setup_failed
goto check_env

:create_python
python -m venv .venv
if errorlevel 1 goto setup_failed

:check_env
".venv\Scripts\python.exe" -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 goto broken_env
".venv\Scripts\python.exe" -c "import av" >nul 2>&1
if not errorlevel 1 goto run
echo Встановлення PyAV. Для першого запуску потрібне підключення до інтернету.
".venv\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto setup_failed

:run
".venv\Scripts\python.exe" -u "python\archival_video_metadata.py" %*
set "RESULT=%ERRORLEVEL%"
goto finish

:broken_env
echo Локальне середовище .venv не працює або містить застарілий Python.
echo Видаліть лише папку .venv і запустіть run.bat повторно.
goto failed

:setup_failed
echo Не вдалося підготувати середовище. Перевірте повідомлення вище,
echo доступ до інтернету, права запису в папку та версію Python.
echo Рекомендовано 64-бітний Python 3.12 або 3.13.

:failed
set "RESULT=1"

:finish
echo.
if "%RESULT%"==2 echo Деякі відео не оброблено. Перегляньте errors.txt у папці поточного звіту.
if "%RESULT%"==1 echo Запуск завершився з помилкою.
if "%RESULT%"==130 echo Обробку перервано.
pause
popd
exit /b %RESULT%
