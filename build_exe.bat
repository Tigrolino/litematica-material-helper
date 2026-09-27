@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo Python isn't on PATH. Install it from python.org first.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 (
    echo Installing dependencies failed.
    pause
    exit /b 1
)

python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "Litematica Material Helper" ^
    --icon "app\assets\icon.ico" ^
    --add-data "app\assets;app\assets" ^
    --collect-all customtkinter ^
    main.py

echo.
if exist "dist\Litematica Material Helper.exe" (
    echo Done: dist\Litematica Material Helper.exe
) else (
    echo Build failed, check the output above.
)
pause
