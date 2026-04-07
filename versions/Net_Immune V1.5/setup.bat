@echo off
echo ===================================================
echo     NET IMMUNE - FIRST TIME SETUP ALGORITHM
echo ===================================================
echo.
echo [1/3] Creating isolated virtual environment...
python -m venv .venv

echo [2/3] Upgrading package manager...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo [3/3] Installing Security AI and UI libraries...
".venv\Scripts\pip.exe" install -r requirements.txt

echo.
echo ===================================================
echo   SETUP COMPLETE! YOU CAN NOW RUN THE APP.
echo ===================================================
pause